# Copyright 2019 CEA
# Author: Yann Leprince <yann.leprince@cea.fr>


def test_config():
    from linear_voluba import create_app
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
