# Copyright 2019 CEA
# Author: Yann Leprince <yann.leprince@cea.fr>


def test_config():
    from linear_voluba import create_app
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200


def test_wsgi_app():
    from linear_voluba.wsgi import application
    assert application is not None


def test_openapi_spec(app, client):
    response = client.get('/openapi.json')
    assert response.status_code == 200
    assert response.json['openapi'] == app.config['OPENAPI_VERSION']
