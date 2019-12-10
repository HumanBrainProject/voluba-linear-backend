# Copyright 2019 CEA
# Author: Yann Leprince <yann.leprince@cea.fr>

"""Module containing a Flask application singleton for use by a WSGI server."""


import linear_voluba
application = linear_voluba.create_app()
