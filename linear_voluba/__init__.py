# Copyright 2019 CEA
# Author: Yann Leprince <yann.leprince@cea.fr>

import logging
import logging.config
import os
import re

import flask


# __version__ and SOURCE_URL are used by setup.py and docs/conf.py (they are
# parsed with a regular expression, so keep the syntax simple).
__version__ = '0.2.0.dev0'


class DefaultConfig:
    # Passed as the 'origins' parameter to flask_cors.CORS, see
    # https://flask-cors.readthedocs.io/en/latest/api.html#flask_cors.CORS
    CORS_ORIGINS = '*'
    # Set to True to enable the /echo endpoint (for debugging)
    ENABLE_ECHO = False
    # Set up werkzeug.middleware.proxy_fix.ProxyFix with the provided keyword
    # arguments, see
    # https://werkzeug.palletsprojects.com/en/0.15.x/middleware/proxy_fix/
    PROXY_FIX = None


# This function has a magic name which is recognized by flask as a factory for
# the main app.
def create_app(test_config=None):
    """Instantiate the voluba-linear-backend Flask application."""
    # logging configuration inspired by
    # http://flask.pocoo.org/docs/1.0/logging/#basic-configuration
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,  # preserve Gunicorn loggers
        'formatters': {'default': {
            'format': '[%(asctime)s] [%(process)d] %(levelname)s '
                      'in %(module)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S %z',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'DEBUG',
            'handlers': ['wsgi']
        }
    })

    # If we are running under Gunicorn, set up the root logger to use the same
    # handler as the Gunicorn error stream.
    if logging.getLogger('gunicorn.error').handlers:
        root_logger = logging.getLogger()
        root_logger.handlers = logging.getLogger('gunicorn.error').handlers
        root_logger.setLevel(logging.getLogger('gunicorn.error').level)

    # Hide Kubernetes health probes from the logs
    access_logger = logging.getLogger('gunicorn.access')
    exclude_useragent_re = re.compile(r'kube-probe')
    access_logger.addFilter(
        lambda record: not (
            record.args['h'].startswith('10.')
            and record.args['m'] == 'GET'
            and record.args['U'] == '/health'
            and exclude_useragent_re.search(record.args['a'])
        )
    )

    app = flask.Flask(__name__,
                      instance_path=os.environ.get("INSTANCE_PATH"),
                      instance_relative_config=True)
    app.config.from_object(DefaultConfig)
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
        app.config.from_envvar("VOLUBA_LINEAR_BACKEND_SETTINGS", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure that the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Return success if the app is ready to serve requests. Used in OpenShift
    # health checks.
    @app.route("/health")
    def health():
        return '', 200

    if app.config.get('ENABLE_ECHO'):
        @app.route('/echo')
        def echo():
            app.logger.info('ECHO:\n'
                            'Headers\n'
                            '=======\n'
                            '%s', flask.request.headers)
            return ''

    if app.config.get('CORS_ORIGINS'):
        import flask_cors
        flask_cors.CORS(app, origins=app.config['CORS_ORIGINS'])

    # TODO: switch to using a blueprint?
    from .api import register_api
    register_api(app, prefix='/api')

    if app.config.get('PROXY_FIX'):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, **app.config['PROXY_FIX'])

    return app
