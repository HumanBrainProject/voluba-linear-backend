import logging
import math

import flask
import flask.views
from flask import json, jsonify, request
import marshmallow
from marshmallow import Schema, fields
from marshmallow.validate import Length, OneOf, Range
import numpy
import numpy as np

from . import leastsquares


logger = logging.getLogger(__name__)

bp = flask.Blueprint('api', __name__, url_prefix='/api')

# Standard codes
HTTP_200_OK = 200
HTTP_501_NOT_IMPLEMENTED = 501


class LandmarkPairSchema(Schema):
    source_point = fields.List(fields.Float, validate=Length(equal=3),
                               required=True)
    target_point = fields.List(fields.Float, validate=Length(equal=3),
                               required=True)
    active = fields.Boolean(default=True, missing=True)
    name = fields.String()
    mismatch = fields.Float(validate=Range(min_inclusive=0.0),
                            dump_only=True, required=True)


class LeastSquaresRequestSchema(Schema):
    class Meta:
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
    )
    landmark_pairs = fields.Nested(
        LandmarkPairSchema,
        many=True, unknown=marshmallow.EXCLUDE, required=True,
    )


class TransformationMatrixField(marshmallow.fields.Field):
    """Field type for a 3D affine matrix (4×4 in homogeneous coordinates)."""

    default_error_messages = {
        'not_an_array': 'Not convertible to a matrix.',
        'invalid_shape': 'Invalid shape (must be 3×4 or 4×4).',
        'invalid_last_row': 'Invalid last row (must be [0, 0, 0, 1]).',
    }

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return leastsquares.np_matrix_to_json(value)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            array = numpy.asarray(value)
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
    transformation_matrix = TransformationMatrixField(required=True)
    inverse_matrix = TransformationMatrixField(required=True)
    landmark_pairs = fields.Nested(
        LandmarkPairSchema,
        many=True, unknown=marshmallow.RAISE, required=True,
    )
    RMSE = fields.Float(validate=Range(min_inclusive=0.0),
                        required=True)


class LeastSquaresAPI(flask.views.MethodView):
    def post(self):
        """
        Calculate an affine transformation matrix from a set of landmarks.
        """
        schema = LeastSquaresRequestSchema()
        params = schema.load(request.json)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Received request on /api/least-squares: %s',
                         json.dumps(params))
        transformation_type = params['transformation_type']
        landmark_pairs = params['landmark_pairs']
        source_points = np.array([pair['source_point']
                                  for pair in landmark_pairs
                                  if pair['active']])
        target_points = np.array([pair['target_point']
                                  for pair in landmark_pairs
                                  if pair['active']])

        if transformation_type == 'rigid':
            mat = leastsquares.umeyama(source_points, target_points,
                                       estimate_scale=False,
                                       allow_reflection=False)
        elif transformation_type == 'rigid+reflection':
            mat = leastsquares.umeyama(source_points, target_points,
                                       estimate_scale=False,
                                       allow_reflection=True)
        elif transformation_type == 'similarity':
            mat = leastsquares.umeyama(source_points, target_points,
                                       estimate_scale=True,
                                       allow_reflection=False)
        elif transformation_type == 'similarity+reflection':
            mat = leastsquares.umeyama(source_points, target_points,
                                       estimate_scale=True,
                                       allow_reflection=True)
        elif transformation_type == 'affine':
            mat = leastsquares.affine(source_points, target_points)

        inv_mat = np.linalg.inv(mat)

        mismatches = leastsquares.per_landmark_mismatch(
            source_points, target_points, mat)
        for pair, mismatch in zip(landmark_pairs, mismatches):
            pair['mismatch'] = mismatch
        rmse = math.sqrt(np.mean(mismatches ** 2))

        if np.all(np.isfinite(mat)) and np.all(np.isfinite(inv_mat)):
            return (
                LeastSquaresResponseSchema().dump({
                    'transformation_matrix': mat,
                    'inverse_matrix': inv_mat,
                    'landmark_pairs': landmark_pairs,
                    'RMSE': rmse,
                }),
                HTTP_200_OK,
            )
        else:
            # FIXME: this should probably not return a 200 code
            return {'error': 'cannot compute least-squares solution '
                             '(singular matrix?)'}, HTTP_200_OK


bp.add_url_rule('/least-squares',
                view_func=LeastSquaresAPI.as_view('least-squares'))


@bp.errorhandler(marshmallow.exceptions.ValidationError)
def handle_validation_error(exc):
    return jsonify({'errors': exc.messages}), 400
