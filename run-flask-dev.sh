#! /bin/sh -e

PYTHONPATH=$(dirname -- "$0")${PYTHONPATH+:}$PYTHONPATH
FLASK_APP=linear_voluba
FLASK_ENV=development
export PYTHONPATH FLASK_APP FLASK_ENV

flask run "$@"
