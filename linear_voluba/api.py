import logging
import math

import flask
from flask import json, jsonify
import flask_restful
from flask_restful import Resource, request
import marshmallow
from marshmallow import Schema, fields
from marshmallow.validate import Length, OneOf
import numpy as np

from . import leastsquares


logger = logging.getLogger(__name__)

bp = flask.Blueprint('api', __name__, url_prefix='/api')
api = flask_restful.Api(bp)

# Standard codes
HTTP_200_OK = 200
HTTP_501_NOT_IMPLEMENTED = 501


class LandmarkPairSchema(Schema):
    source_point = fields.List(fields.Float, validate=Length(equal=3),
                               required=True)
    target_point = fields.List(fields.Float, validate=Length(equal=3),
                               required=True)
    active = fields.Boolean(default=True)
    name = fields.String()


class LeastSquaresRequestSchema(Schema):
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


class LeastSquaresAPI(Resource):
    def post(self):
        """
        Calculate an affine transformation matrix from a set of landmarks.
        """
        schema = LeastSquaresRequestSchema()
        params = schema.load(request.json, unknown=marshmallow.EXCLUDE)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Received request on /api/least-squares: %s',
                         json.dumps(request.json))
        transformation_type = params['transformation_type']
        landmark_pairs = params['landmark_pairs']
        source_points = np.array([pair['source_point']
                                  for pair in landmark_pairs])
        target_points = np.array([pair['target_point']
                                  for pair in landmark_pairs])

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
            transformation_matrix = leastsquares.np_matrix_to_json(mat)
            inverse_matrix = leastsquares.np_matrix_to_json(inv_mat)
            return ({'transformation_matrix': transformation_matrix,
                     'inverse_matrix': inverse_matrix,
                     'landmark_pairs': landmark_pairs,
                     'RMSE': rmse},
                    HTTP_200_OK)
        else:
            return {'error': 'cannot compute least-squares solution '
                             '(singular matrix?)'}, HTTP_200_OK


api.add_resource(LeastSquaresAPI, '/least-squares')


@bp.errorhandler(marshmallow.exceptions.ValidationError)
def handle_validation_error(exc):
    return jsonify({'errors': exc.messages}), 400
