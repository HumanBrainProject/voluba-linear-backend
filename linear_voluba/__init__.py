import flask

from .api import register_api


# __version__ and SOURCE_URL are used by setup.py and docs/conf.py (they are
# parsed with a regular expression, so keep the syntax simple).
__version__ = '0.2.0.dev0'


app = flask.Flask(__name__, static_folder='../frontend/dist')


@app.route("/")
def root():
    return app.send_static_file('index.html')

# Return success if the app is ready to serve requests. Used in OpenShift
# health checks.
@app.route("/health")
def health():
    return '', 200


register_api(app, prefix='/api')
