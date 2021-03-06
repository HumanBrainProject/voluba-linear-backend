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

import logging
import math

import flask
import flask.views
from flask import json, request
import flask_smorest
from flask_smorest import abort
import marshmallow
from marshmallow import Schema, fields
from marshmallow.validate import Length, OneOf, Range
import numpy
import numpy as np

from . import leastsquares


logger = logging.getLogger(__name__)

bp = flask_smorest.Blueprint(
    'api', __name__, url_prefix='/api',
    description='API of the Voluba linear backend (backward-compatible with '
                'landmark-reg)',
)


class LandmarkPairSchema(Schema):
    class Meta:
        ordered = True
    source_point = fields.List(
        fields.Float, validate=Length(equal=3), required=True,
        description='Coordinates of the point in source space.',
    )
    target_point = fields.List(
        fields.Float, validate=Length(equal=3), required=True,
        description='Coordinates of the point in target space.',
    )
    active = fields.Boolean(
        default=True, missing=True,
        description='Landmark pairs for which active is false are not used '
                    'for the estimation of the transformation matrix.',
    )
    name = fields.String(
        required=False,
        description='Optional identifier of the landmark pair.',
    )
    mismatch = fields.Float(
        validate=Range(min_inclusive=0.0), dump_only=True, required=True,
        description='Euclidean distance, in the target space, between the '
                    '`target_point` and the `source_point` transformed by '
                    '`transformation_matrix`',
    )


class LeastSquaresRequestSchema(Schema):
    class Meta:
        ordered = True
        unknown = marshmallow.EXCLUDE
    transformation_type = fields.String(
        validate=OneOf([
            'rigid',
            'rigid+reflection',
            'similarity',
            'similarity+reflection',
            'affine',
        ]),
        required=True,
        description='Method to use for estimating the transformation matrix '
                    '(see the documentation of `/api/least-squares`).',
    )
    landmark_pairs = fields.Nested(
        LandmarkPairSchema,
        many=True, unknown=marshmallow.EXCLUDE, required=True,
        description='List of landmark pairs to use in the estimation.',
    )


class TransformationMatrixField(marshmallow.fields.Field):
    """Field type for a 3D affine matrix (4×4 in homogeneous coordinates)."""

    default_error_messages = {
        'not_an_array': 'Not convertible to a matrix.',
        'invalid_shape': 'Invalid shape (must be 3×4 or 4×4).',
        'invalid_last_row': 'Invalid last row (must be [0, 0, 0, 1]).',
    }

    def __init__(self, **kwargs):
        # Add metadata fields for apispec to generate an accurate OpenAPI spec
        new_kwargs = {
            'type': 'array',
            'minItems': 3,
            'maxItems': 4,
            'items': {
                "minItems": 4,
                "maxItems": 4,
                "type": "array",
                "items": {
                    "format": "float",
                    "type": "number"
                },
            },
        }
        new_kwargs.update(kwargs)
        super().__init__(**new_kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return leastsquares.np_matrix_to_json(value)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            array = numpy.asarray(value, dtype=float)
        except Exception as exc:
            raise self.make_error('not_an_array') from exc
        if array.shape not in [(3, 4), (4, 4)]:
            raise self.make_error('invalid_shape')
        if array.shape[0] == 3:
            array = numpy.r_[array, [[0, 0, 0, 1]]]
        elif not numpy.array_equal(array[3], [0, 0, 0, 1]):
            raise self.make_error('invalid_last_row')
        return array


class LeastSquaresResponseSchema(Schema):
    class Meta:
        ordered = True
    transformation_matrix = TransformationMatrixField(
        required=True,
        description='Transformation matrix from source space to target space.',
    )
    inverse_matrix = TransformationMatrixField(
        required=True,
        description='Transformation matrix from target space to source space.',
    )
    landmark_pairs = fields.Nested(
        LandmarkPairSchema,
        many=True, unknown=marshmallow.RAISE, required=True,
        description='The list of landmark pairs that were sent in the '
                    'request (including pairs for which `active` is false). '
                    'Any unknown fields that were sent in the request are '
                    'omitted, and the `mismatch` field is added.',
    )
    RMSE = fields.Float(
        validate=Range(min_inclusive=0.0), required=True,
        description='RMSE (root mean square error) is the root mean square '
                    'average of all `mismatch` values (including those for '
                    'which `active` is false).',
    )


class ErrorResponseSchema(Schema):
    class Meta:
        ordered = True
        unknown = marshmallow.INCLUDE
        strict = False
    code = fields.Integer(required=False)
    status = fields.String(required=False)
    message = fields.String(required=False)
    errors = fields.Dict(keys=fields.String(), required=False)


@bp.route('/least-squares')
class LeastSquaresAPI(flask.views.MethodView):
    @bp.arguments(LeastSquaresRequestSchema, location='json',
                  example={
                      'transformation_type': 'similarity+reflection',
                      'landmark_pairs': [
                          {
                              'source_point': [0, 0, 0],
                              'target_point': [10, 10, 10],
                          },
                          {
                              'source_point': [1, 0, 0],
                              'target_point': [8, 10, 10],
                          },
                          {
                              'source_point': [0, 1, 0],
                              'target_point': [10, 12, 10],
                          },
                          {
                              'source_point': [0, 0, -1],
                              'target_point': [10, 10, 12],
                          },
                      ],
                  })
    # The error responses come first, the schemas are only used for
    # documentation
    @bp.response(ErrorResponseSchema,
                 code=400,
                 example={'message': 'cannot compute least-squares solution '
                                     '(singular matrix?)'})
    # Code 422 is raised by webargs for request validation errors
    @bp.response(ErrorResponseSchema,
                 code=422, description='Semantically invalid request')
    # The successful response must be the last response decorator, its schema
    # is used for serializing the response.
    @bp.response(LeastSquaresResponseSchema,
                 example={
                     'transformation_matrix': [
                         [-2, 0, 0, 10],
                         [0, 2, 0, 10],
                         [0, 0, -2, 10],
                         [0, 0, 0, 1]
                     ],
                     'inverse_matrix': [
                         [-0.5, 0, 0, 5],
                         [0, 0.5, 0, -5],
                         [0, 0, -0.5, 5],
                         [0, 0, 0, 1]
                     ],
                     'RMSE': 0,
                     'landmark_pairs': [
                         {
                             'active': True,
                             'mismatch': 0,
                             'source_point': [0, 0, 0],
                             'target_point': [10, 10, 10],
                         },
                         {
                             'active': True,
                             'mismatch': 0,
                             'source_point': [1, 0, 0],
                             'target_point': [8, 10, 10],
                         },
                         {
                             'active': True,
                             'mismatch': 0.0,
                             'source_point': [0, 1, 0],
                             'target_point': [10, 12, 10],
                         },
                         {
                             'active': True,
                             'mismatch': 0.0,
                             'source_point': [0, 0, -1],
                             'target_point': [10, 10, 12],
                         },
                     ],
                 })
    def post(self, args):
        """Calculate an affine transformation matrix from a set of landmarks.

        This endpoint calculates an affine transformation matrix that maps a 3D
        source space to a 3D target space, using a list of corresponding points
        as input (`landmark_pairs`).

        The resulting matrix is returned in the formalism of homogeneous
        coordinates: it is a 4×4 matrix where the last row is always `[0, 0, 0,
        1]`. The 3×3 submatrix contains the rotation, scaling, inversion, and
        shearing parameters, and the 3×1 vector on the last column contains the
        translation coefficients.

        ### Methods

        Several methods are available for the matrix estimation, which are all
        based on solving a least-squares problem. The available methods are:

        - `rigid+reflection` and `rigid`, which estimate a 6-parameter rigid
           transformation (3 translation parameters and 3 rotation parameters).
           The `rigid` variant forces a proper rotation (determinant = +1),
           whereas `rigid+reflection` allows an inversion (determinant = ±1).

        - `rigid+reflection` and `rigid`, which estimate a 7-parameter
           siminality transformation (3 translation parameters, 1 scaling
           factor, and 3 rotation parameters). The `similarity` variant forces
           a proper rotation (determinant > 0), whereas `similarity+reflection`
           allows an axis inversion.

        - `affine`, which estimates a full 12-parameter affine transformation.
          Such a transformation can apply translation, rotation, inversion,
          anisotropic scaling, and shearing.

        Each method needs a minimal number of linearly independent
        (non-collinear and non-coplanar) landmark pairs, below this number the
        endpoint will return a 400 code and include an informative error
        message in the `message` field of the response:
        - 3 points are needed for `rigid` and `similarity`,
        - 4 points are needed for `rigid+reflection`, `similarity+reflection`,
          and `affine`.

        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Received request on /api/least-squares: %s',
                         json.dumps(request.json))
        transformation_type = args['transformation_type']
        landmark_pairs = args['landmark_pairs']
        source_points = np.array([pair['source_point']
                                  for pair in landmark_pairs
                                  if pair['active']])
        target_points = np.array([pair['target_point']
                                  for pair in landmark_pairs
                                  if pair['active']])

        try:
            if transformation_type == 'rigid':
                mat = leastsquares.extended_umeyama(
                    source_points, target_points,
                    estimate_scale=False, allow_reflection=False
                )
            elif transformation_type == 'rigid+reflection':
                mat = leastsquares.extended_umeyama(
                    source_points, target_points,
                    estimate_scale=False, allow_reflection=True
                )
            elif transformation_type == 'similarity':
                mat = leastsquares.extended_umeyama(
                    source_points, target_points,
                    estimate_scale=True, allow_reflection=False
                )
            elif transformation_type == 'similarity+reflection':
                mat = leastsquares.extended_umeyama(
                    source_points, target_points,
                    estimate_scale=True, allow_reflection=True
                )
            elif transformation_type == 'affine':
                mat = leastsquares.affine(source_points, target_points)
        except leastsquares.UnderdeterminedProblem as exc:
            abort(400, message=str(exc))

        inv_mat = np.linalg.inv(mat)

        mismatches = leastsquares.per_landmark_mismatch(
            source_points, target_points, mat)
        for pair, mismatch in zip(landmark_pairs, mismatches):
            pair['mismatch'] = mismatch
        rmse = math.sqrt(np.mean(mismatches ** 2))

        assert np.all(np.isfinite(mat)) and np.all(np.isfinite(inv_mat))
        return {
            'transformation_matrix': mat,
            'inverse_matrix': inv_mat,
            'landmark_pairs': landmark_pairs,
            'RMSE': rmse,
        }
