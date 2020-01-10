# Copyright 2019–2020 CEA
# Copyright 2017 Forschungszentrum Jülich GmbH
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

import json
import numpy
import pytest

from linear_voluba import leastsquares


def apply_transform_to_points(transform_matrix, points):
    if points.shape[1] < transform_matrix.shape[1]:
        points = numpy.c_[points, numpy.ones(len(points))]
    homogeneous_result = transform_matrix @ points.T
    return (homogeneous_result[:-1] / homogeneous_result[-1]).T


SOURCE_POINTS = numpy.array([
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
    [0.5, 0.5, 0.5],
])

TEST_RIGID_MATRIX = numpy.array([
    [ 0.936293, -0.189796,  0.295520,   2.],  # noqa: E201, E202
    [ 0.313205,  0.831942, -0.458013,  33.],  # noqa: E201, E202
    [-0.158927,  0.521393,  0.838387, 100.],  # noqa: E201, E202
    [ 0.0     ,  0.0     ,   0.0    ,   1.]   # noqa: E201, E202
])

TEST_RIGID_AND_MIRROR_MATRIX = numpy.array([
    [ 0.936293, -0.189796, -0.295520,   2.],  # noqa: E201, E202
    [ 0.313205,  0.831942,  0.458013,  33.],  # noqa: E201, E202
    [-0.158927,  0.521393, -0.838387, 100.],  # noqa: E201, E202
    [ 0.0     ,  0.0     ,   0.0    ,   1.]   # noqa: E201, E202
])

TEST_SIMILARITY_MATRIX = numpy.array([
    [ 0.749035, -0.151837,  0.236416,   2.],  # noqa: E201, E202
    [ 0.250564,  0.665554, -0.36641 ,  33.],  # noqa: E201, E202
    [-0.127141,  0.417114,  0.670709, 100.],  # noqa: E201, E202
    [ 0.0     ,  0.0     ,  0.0     ,   1.]   # noqa: E201, E202
])

TEST_SIMILARITY_AND_MIRROR_MATRIX = numpy.array([
    [ 0.749035, -0.151837, -0.236416,   2.],  # noqa: E201, E202
    [ 0.250564,  0.665554,  0.36641 ,  33.],  # noqa: E201, E202
    [-0.127141,  0.417114, -0.670709, 100.],  # noqa: E201, E202
    [ 0.0     ,  0.0     ,  0.0     ,   1.]   # noqa: E201, E202
])

TEST_AFFINE_MATRIX = numpy.array([
    [1.2, 0.8, 0.9, 2.0  ],  # noqa: E201, E202
    [0.7, 1.1, 1.2, 33.0 ],  # noqa: E201, E202
    [1.1, 0.9, 0.8, 100.0],  # noqa: E201, E202
    [0.0, 0.0, 0.0, 1.0  ]   # noqa: E201, E202
])


@pytest.mark.parametrize('point_count', [4, 5])
def test_affine_estimation(point_count):
    test_matrix = TEST_AFFINE_MATRIX
    source_points = SOURCE_POINTS[:point_count]
    transformed_points = apply_transform_to_points(test_matrix, source_points)
    estimated_matrix = leastsquares.affine(source_points, transformed_points)
    assert numpy.allclose(test_matrix, estimated_matrix)


@pytest.mark.parametrize('point_count', [4, 5])
def test_affine_estimation_in_source_space(point_count):
    test_matrix = TEST_AFFINE_MATRIX
    source_points = SOURCE_POINTS[:point_count]
    transformed_points = apply_transform_to_points(test_matrix, source_points)
    estimated_matrix = leastsquares.affine_gergely(source_points,
                                                   transformed_points)
    assert numpy.allclose(test_matrix, estimated_matrix)


@pytest.mark.parametrize(
    ['estimate_scale', 'allow_reflection', 'point_count'],
    [
        (False, False, 3),
        (False, False, 4),
        (True, False, 3),
        (True, False, 4),
        (False, True, 4),
        (False, True, 5),
        (True, True, 4),
        (True, True, 5),
    ]
)
def test_extended_umeyama_rigid_estimation(estimate_scale,
                                           allow_reflection,
                                           point_count):
    test_matrix = TEST_RIGID_MATRIX
    source_points = SOURCE_POINTS[:point_count]
    transformed_points = apply_transform_to_points(test_matrix, source_points)
    estimated_matrix = leastsquares.extended_umeyama(
        source_points, transformed_points,
        estimate_scale=estimate_scale,
        allow_reflection=allow_reflection,
    )
    assert numpy.allclose(test_matrix, estimated_matrix)


@pytest.mark.parametrize(
    ['estimate_scale', 'allow_reflection', 'point_count'],
    [
        (False, True, 4),
        (False, True, 5),
        (True, True, 4),
        (True, True, 5),
    ]
)
def test_extended_umeyama_rigid_and_mirror_estimation(estimate_scale,
                                                      allow_reflection,
                                                      point_count):
    test_matrix = TEST_RIGID_AND_MIRROR_MATRIX
    source_points = SOURCE_POINTS[:point_count]
    transformed_points = apply_transform_to_points(test_matrix, source_points)
    estimated_matrix = leastsquares.extended_umeyama(
        source_points, transformed_points,
        estimate_scale=estimate_scale,
        allow_reflection=allow_reflection,
    )
    assert numpy.allclose(test_matrix, estimated_matrix)


@pytest.mark.parametrize(
    ['estimate_scale', 'allow_reflection', 'point_count'],
    [
        (True, False, 3),
        (True, False, 4),
        (True, True, 4),
        (True, True, 5),
    ]
)
def test_extended_umeyama_similarity_estimation(estimate_scale,
                                                allow_reflection,
                                                point_count):
    test_matrix = TEST_SIMILARITY_MATRIX
    source_points = SOURCE_POINTS[:point_count]
    transformed_points = apply_transform_to_points(test_matrix, source_points)
    estimated_matrix = leastsquares.extended_umeyama(
        source_points, transformed_points,
        estimate_scale=estimate_scale,
        allow_reflection=allow_reflection,
    )
    assert numpy.allclose(test_matrix, estimated_matrix)


@pytest.mark.parametrize('point_count', [4, 5])
def test_extended_umeyama_similarity_and_mirror_estimation(point_count):
    test_matrix = TEST_SIMILARITY_AND_MIRROR_MATRIX
    source_points = SOURCE_POINTS[:point_count]
    transformed_points = apply_transform_to_points(test_matrix, source_points)
    estimated_matrix = leastsquares.extended_umeyama(
        source_points, transformed_points,
        estimate_scale=True,
        allow_reflection=True,
    )
    assert numpy.allclose(test_matrix, estimated_matrix)


def test_numpy_matrix_to_json():
    test_matrix = TEST_AFFINE_MATRIX
    json_matrix = leastsquares.np_matrix_to_json(test_matrix)
    encoded_matrix = json.dumps(json_matrix)
    decoded_matrix = json.loads(encoded_matrix)
    assert numpy.array_equal(numpy.array(decoded_matrix), test_matrix)


def test_per_landmark_mismatch():
    test_matrix = numpy.array(
        [[1.0, 0.0, 0.0,  0.0],
         [0.0, 2.0, 0.0,  0.0],
         [0.0, 0.0, 1.0, 10.0],
         [0.0, 0.0, 0.0, 1.0 ]]  # noqa: E201, E202
    )
    dest_points = numpy.array([
        [0, 0, 10],
        [1, 0, 9],
        [0, 1, 10],
        [0, 0, 11],
        [0.5, 3.0, 10.5],
    ])
    mismatch = leastsquares.per_landmark_mismatch(SOURCE_POINTS,
                                                  dest_points,
                                                  test_matrix)
    assert numpy.allclose(mismatch, [0, 1, 1, 0, 2])


COPLANAR_POINTS = numpy.array([
    [0, 0, 0],
    [1, 0, 0],
    [2, 0, 0],
    [0, 1, 0],
])

TRANSFORMED_COPLANAR_POINTS = apply_transform_to_points(
    TEST_RIGID_MATRIX,
    COPLANAR_POINTS
)


@pytest.mark.parametrize(
    ['estimate_scale', 'allow_reflection', 'point_count'],
    [
        (False, False, 0),
        (False, False, 1),
        (False, False, 2),
        (False, False, 3),
        (True, False, 2),
        (True, False, 3),
        (False, True, 3),
        (False, True, 4),
        (True, True, 3),
        (True, True, 4),
    ]
)
def test_underconstrained_extended_umeyama(estimate_scale,
                                           allow_reflection,
                                           point_count):
    with pytest.raises(leastsquares.UnderdeterminedProblem):
        leastsquares.extended_umeyama(
            COPLANAR_POINTS[:point_count],
            TRANSFORMED_COPLANAR_POINTS[:point_count],
            estimate_scale=estimate_scale,
            allow_reflection=allow_reflection,
        )


OVERCONSTRAINED_SOURCE_POINTS = numpy.array([
    [0, 0, 0],
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
])
OVERCONSTRAINED_TARGET_POINTS = numpy.array([
    [0, 0, 0],
    [1, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
])


@pytest.mark.parametrize('estimate_scale', [False, True])
@pytest.mark.parametrize('allow_reflection', [False, True])
def test_overconstrained_extended_umeyama(estimate_scale,
                                          allow_reflection):
    # The modified Umeyama method does not detect overconstrained cases
    leastsquares.extended_umeyama(
        OVERCONSTRAINED_SOURCE_POINTS,
        OVERCONSTRAINED_TARGET_POINTS,
        estimate_scale=estimate_scale,
        allow_reflection=allow_reflection,
    )


@pytest.mark.skip('FIXME: underconstrained not detected by affine yet')
@pytest.mark.parametrize('point_count', list(range(5)))
def test_underconstrained_affine(point_count):
    with pytest.raises(leastsquares.UnderdeterminedProblem):
        leastsquares.affine(COPLANAR_POINTS[:point_count],
                            TRANSFORMED_COPLANAR_POINTS[:point_count])


def test_overconstrained_affine():
    leastsquares.affine(
        OVERCONSTRAINED_SOURCE_POINTS,
        OVERCONSTRAINED_TARGET_POINTS,
    )


@pytest.mark.parametrize('point_count', [3, 4])
def test_underconstrained_affine_in_source_space(point_count):
    with pytest.raises(numpy.linalg.LinAlgError):
        leastsquares.affine_gergely(COPLANAR_POINTS[:point_count],
                                    TRANSFORMED_COPLANAR_POINTS[:point_count])
