# Copyright 2017–2019 Forschungszentrum Jülich GmbH
# Copyright 2019–2020 CEA
#
# Author: Yann Leprince <yann.leprince@cea.fr>
#
# Licensed under the Apache Licence, Version 2.0 (the "Licence");
# you may not use this file except in compliance with the Licence.
# You may obtain a copy of the Licence at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and
# limitations under the Licence.

import datetime
import logging
import logging.config
import os
import re

import flask
import flask_smorest


# __version__ and SOURCE_URL are used by setup.py and docs/conf.py (they are
# parsed with a regular expression, so keep the syntax simple).
__version__ = '0.2.0.dev0'

SOURCE_URL = 'https://github.com/HumanBrainProject/voluba-linear-backend'
"""URL that holds the source code of the backend.

This should be changed to point to the code of any modified version.
"""


class DefaultConfig:
    # Passed as the 'origins' parameter to flask_cors.CORS, see
    # https://flask-cors.readthedocs.io/en/latest/api.html#flask_cors.CORS
    CORS_ORIGINS = '*'
    # Duration that the browser is allowed to cache the results of a CORS
    # preflight request.
    CORS_MAX_AGE = datetime.timedelta(minutes=10)
    # Set to True to enable the /echo endpoint (for debugging)
    ENABLE_ECHO = False
    # Set up werkzeug.middleware.proxy_fix.ProxyFix with the provided keyword
    # arguments, see
    # https://werkzeug.palletsprojects.com/en/0.15.x/middleware/proxy_fix/
    PROXY_FIX = None
    # Version of the linear_voluba api (used in the OpenAPI spec)
    API_VERSION = __version__
    OPENAPI_VERSION = '3.0.2'  # OpenAPI version to generate
    OPENAPI_URL_PREFIX = '/'
    OPENAPI_REDOC_PATH = 'redoc'
    OPENAPI_REDOC_VERSION = '2.0.0-rc.20'
    OPENAPI_SWAGGER_UI_PATH = 'swagger-ui'
    OPENAPI_SWAGGER_UI_VERSION = '3.24.2'


# This function has a magic name which is recognized by flask as a factory for
# the main app.
def create_app(test_config=None):
    """Instantiate the voluba-linear-backend Flask application."""
    # logging configuration inspired by
    # http://flask.pocoo.org/docs/1.0/logging/#basic-configuration
    if test_config is None or not test_config.get('TESTING'):
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

    @app.route("/")
    def root():
        return flask.redirect('/redoc')

    @app.route("/source")
    def source():
        return flask.redirect(SOURCE_URL)

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
        flask_cors.CORS(app, origins=app.config['CORS_ORIGINS'],
                        max_age=app.config['CORS_MAX_AGE'])

    if app.config['ENV'] == 'development':
        local_server = [
            {
                'url': '/',
            },
        ]
    else:
        local_server = []

    smorest_api = flask_smorest.Api(app, spec_kwargs={
        'servers': local_server + [
            {
                'url': 'https://voluba-linear-backend.apps.hbp.eu/',
                'description': 'Production instance running the *master* '
                               'branch',
            },
            {
                'url': 'https://voluba-linear-backend.apps-dev.hbp.eu/',
                'description': 'Development instance running the *dev* '
                               'branch',
            },
        ],
        'info': {
            'title': 'voluba-linear-backend',
            'description': '''\
An HTTP backend for estimating linear spatial transformations from a list of
point landmarks.

This backend is used by [Voluba](https://voluba.apps.hbp.eu/), a web-based tool
for interactive registration of 3-dimensional images, dedicated to the
alignment of sub-volumes into brain templates.

For more information, see the **source code repository:** <{SOURCE_URL}>.
'''.format(SOURCE_URL=SOURCE_URL),
            'license': {
                'name': 'Apache 2.0',
                'url': 'https://www.apache.org/licenses/LICENSE-2.0.html',
            },
        },
    })

    from . import api
    smorest_api.register_blueprint(api.bp)

    if app.config.get('PROXY_FIX'):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, **app.config['PROXY_FIX'])

    return app
