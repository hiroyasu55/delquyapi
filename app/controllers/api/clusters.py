from flask import Blueprint, jsonify
import app.lib.log as log
import app.models.Cluster as Cluster

logger = log.getLogger(__name__)
api_clusters = Blueprint('clusters', __name__, url_prefix='/api/clusters')


@api_clusters.route('/', methods=['GET'])
def index():
    clusters = Cluster.find()

    result = {
        'clusters': clusters,
        'status': 'success',
    }
    return jsonify(result)


@api_clusters.route('/<int:no>', methods=['GET'])
def find_by_no(no):
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
    return jsonify(result)


@api_clusters.errorhandler(400)
@api_clusters.errorhandler(404)
def error_400_404(error):
    return jsonify({
        'status': 'failure',
        'code': error.description['code'],
        'message': error.description['message']
    }), error.code


@api_clusters.errorhandler(500)
def error_500(error):
    return jsonify({
        'status': 'failure',
        'code': error.description['code'],
        'message': 'Internal error.'
    }), error.code
