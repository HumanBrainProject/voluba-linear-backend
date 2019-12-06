# Copyright 2019 CEA
# Author: Yann Leprince <yann.leprince@cea.fr>

import pytest

import linear_voluba


@pytest.fixture
def app():
    # FIXME: refactoring in progress
    # app = linear_voluba.create_app({
    #     'TESTING': True,
    # })
    app = linear_voluba.app
    return app


@pytest.fixture
def client(app):
    return app.test_client()
