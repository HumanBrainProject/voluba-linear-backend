import logging
import math

import flask
from flask import json
import flask_restful
from flask_restful import Resource, request
import numpy as np

from . import leastsquares


logger = logging.getLogger(__name__)

bp = flask.Blueprint('api', __name__, url_prefix='/api')
api = flask_restful.Api(bp)

# Standard codes
HTTP_200_OK = 200
HTTP_501_NOT_IMPLEMENTED = 501


class LeastSquaresAPI(Resource):
    def post(self):
        """
        Calculate an affine transformation matrix from a set of landmarks.
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Received request on /api/least-squares: %s',
                         json.dumps(request.json))
        transformation_type = request.json['transformation_type']
        landmark_pairs = request.json['landmark_pairs']
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
        else:
            return ({'error': 'unrecognized transformation_type'},
                    HTTP_501_NOT_IMPLEMENTED)

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
