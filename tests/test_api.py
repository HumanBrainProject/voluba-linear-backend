# Copyright 2019 CEA
# Author: Yann Leprince <yann.leprince@cea.fr>

import numpy
import pytest


# Request sent by the original landmark-reg (AngularJS-based prototype)
TEST_LANDMARK_PAIRS = [
    {
        'active': True,
        'colour': '#8dd3c7',
        'name': 'most medial, inferior point',
        'source_point': [11.4, 8.6, 4.1],
        'target_point': [63.1, 74.7, 47.7],
    },
    {
        'active': True,
        'colour': '#ffffb3',
        'name': 'most lateral, superior point',
        'source_point': [4.1, 4.5, 4.1],
        'target_point': [56.5, 74.7, 52.4],
    },
    {
        'active': True,
        'colour': '#bebada',
        'name': 'most anterior point',
        'source_point': [10.224, 6.752, 9.74],
        'target_point': [62.2, 80.0, 49.5],
    },
    {
        'active': True,
        'colour': '#000000',
        'name': 'other nonsensical point',
        'source_point': [0.0, 1.0, 2.0],
        'target_point': [50.0, 51.0, 52.0],
    },
]


def test_least_squares_full_request(client):
    response = client.post('/api/least-squares', json={
        'landmark_pairs': TEST_LANDMARK_PAIRS,
        'source_image': 'http://h.test/source-image',
        'target_image': 'http://h.test/target-image',
        'transformation_type': 'similarity',
    })
    assert response.status_code == 200

    assert 'transformation_matrix' in response.json
    assert 'inverse_matrix' in response.json
    matrix = numpy.array(response.json['transformation_matrix'])
    inverse_matrix = numpy.array(response.json['inverse_matrix'])
    assert matrix.shape == (4, 4)
    assert inverse_matrix.shape == (4, 4)
    assert numpy.allclose(inverse_matrix @ matrix, numpy.eye(4))
    assert numpy.allclose(matrix @ inverse_matrix, numpy.eye(4))

    assert 'RMSE' in response.json
    assert isinstance(response.json['RMSE'], float)

    assert 'landmark_pairs' in response.json
    assert len(response.json['landmark_pairs']) == len(TEST_LANDMARK_PAIRS)
    for returned_pair, orig_pair in zip(response.json['landmark_pairs'],
                                        TEST_LANDMARK_PAIRS):
        assert 'source_point' in returned_pair
        assert numpy.allclose(returned_pair['source_point'],
                              orig_pair['source_point'])
        assert 'target_point' in returned_pair
        assert numpy.allclose(returned_pair['target_point'],
                              orig_pair['target_point'])
        assert 'mismatch' in returned_pair
        assert isinstance(returned_pair['mismatch'], float)


def test_least_squares_minimal_request(client):
    response = client.post('/api/least-squares', json={
        'landmark_pairs': [
            {
                'source_point': pair['source_point'],
                'target_point': pair['target_point'],
            }
            for pair in TEST_LANDMARK_PAIRS[:3]
        ],
        'transformation_type': 'similarity',
    })
    assert response.status_code == 200

    assert 'transformation_matrix' in response.json
    assert 'inverse_matrix' in response.json
    assert 'RMSE' in response.json
    assert 'landmark_pairs' in response.json
    assert len(response.json['landmark_pairs']) == 3
    for returned_pair, orig_pair in zip(response.json['landmark_pairs'],
                                        TEST_LANDMARK_PAIRS):
        assert 'source_point' in returned_pair
        assert numpy.allclose(returned_pair['source_point'],
                              orig_pair['source_point'])
        assert 'target_point' in returned_pair
        assert numpy.allclose(returned_pair['target_point'],
                              orig_pair['target_point'])
        assert 'mismatch' in returned_pair
        assert isinstance(returned_pair['mismatch'], float)


@pytest.mark.parametrize(
    ['transformation_type', 'point_count'],
    [
        ('rigid', 3),
        ('similarity', 3),
        ('rigid+reflection', 4),
        ('similarity+reflection', 4),
        ('affine', 4),
    ]
)
def test_least_squares_transformation_types(client,
                                            transformation_type,
                                            point_count):
    response = client.post('/api/least-squares', json={
        'landmark_pairs': TEST_LANDMARK_PAIRS[:point_count],
        'transformation_type': transformation_type,
    })
    assert response.status_code == 200


def test_least_squares_invalid_requests(client):
    response = client.get('/api/least-squares')
    assert response.status_code == 405

    response = client.post('/api/least-squares', json={
        'landmark_pairs': TEST_LANDMARK_PAIRS,
        'transformation_type': 'invalid',
    })
    assert 400 <= response.status_code < 500

    response = client.post('/api/least-squares', json={
        'transformation_type': 'invalid',
    })
    assert 400 <= response.status_code < 500

    response = client.post('/api/least-squares', json={
        'landmark_pairs': TEST_LANDMARK_PAIRS,
    })
    assert 400 <= response.status_code < 500

    response = client.post('/api/least-squares', json={})
    assert 400 <= response.status_code < 500


def test_transformation_matrix_field():
    import marshmallow
    from marshmallow.exceptions import ValidationError
    from linear_voluba.api import TransformationMatrixField

    class TestSchema(marshmallow.Schema):
        val = TransformationMatrixField()

    schema = TestSchema()
    mat = schema.load({'val': [[1, 0, 0, 0],
                               [0, 1, 0, 0],
                               [0, 0, 1, 0],
                               [0, 0, 0, 1]]})
    assert isinstance(mat['val'], numpy.ndarray)
    assert numpy.array_equal(mat['val'], numpy.eye(4))
    mat = schema.load({'val': [[1, 0, 0, 0],
                               [0, 1, 0, 0],
                               [0, 0, 1, 0]]})
    assert isinstance(mat['val'], numpy.ndarray)
    assert numpy.array_equal(mat['val'], numpy.eye(4))

    serialized = schema.dump({'val': numpy.eye(4)})
    assert serialized == {
        'val': [[1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]],
    }

    with pytest.raises(ValidationError):
        schema.load({'val': 'string'})
    with pytest.raises(ValidationError):
        schema.load({'val': {'some': 'dict'}})
    with pytest.raises(ValidationError):
        schema.load({'val': None})
    with pytest.raises(ValidationError):
        schema.load({'val': []})
    with pytest.raises(ValidationError):
        schema.load({'val': [[1, 2], [3]]})
    with pytest.raises(ValidationError):
        schema.load({'val': [[1, 0, 0, 0],
                             [0, 1, 0, 0],
                             [0, 0, 1, 0],
                             [1, 2, 3, 4]]})

    # Test the OpenAPI fields supplied as metadata. TODO: test actual
    # conversion to JSON Schema using apispec.
    assert schema.fields['val'].metadata['type'] == 'array'
    assert schema.fields['val'].metadata['minItems'] == 3
    assert schema.fields['val'].metadata['maxItems'] == 4
    assert schema.fields['val'].metadata['items'] == {
        "type": "array",
        "minItems": 4,
        "maxItems": 4,
        "items": {
            "format": "float",
            "type": "number"
        },
    }
