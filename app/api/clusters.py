from flask import jsonify, request
from flask_restful import Resource
import app.lib.log as log
import app.models.Cluster as Cluster

logger = log.getLogger(__name__)


class ClustersApi(Resource):
    def get(self, no=None):
        result = {}

        if no:
            result = self._find_by_no(no)

        else:
            result = self._find(request.args)

        return jsonify(result)

    def _find(self, args):
        clusters = Cluster.find()

        result = {
            'clusters': clusters,
            'status': 'success',
        }
        return result

    def _find_by_no(self, no):
        cluster = Cluster.find_by_no(no)

        if not cluster:
            return {
                'status': 'failure',
                'message': 'Cluster not found.'
            }

        result = {
            'status': 'success',
            'cluster': cluster
        }
        return result
