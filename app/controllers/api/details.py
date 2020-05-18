from flask import Blueprint, jsonify, request
import app.lib.log as log
import app.models.Detail as Detail

logger = log.getLogger(__name__)
api_details = Blueprint('details', __name__, url_prefix='/api/details')


@api_details.route('/', methods=['GET'])
def index():
    filters = []
    offset = request.args.get('offset', '')
    offset = int(offset) if str.isdecimal(offset) else 0
    limit = request.args.get('limit', '')
    limit = int(limit) if str.isdecimal(limit) else None

    details = Detail.find(filters=filters, offset=offset, limit=limit)
    total = Detail.count(filters=filters)

    result = {
        'status': 'success',
        'details': details,
        'total': total
    }
    return jsonify(result)


@api_details.route('/<id>', methods=['GET'])
def detail(id):
    detail = Detail.find_by_id(id)
    if not detail:
        return {
            'status': 'failure',
            'message': 'Detail[{}] not found.'.format(id)
        }

    result = {
        'status': 'success',
        'detail': detail
    }
    return jsonify(result)


@api_details.route('/<government>/<int:no>', methods=['GET'])
def detail_govenment_no(government, no):
    detail = Detail.find_by_government_no(government, no)
    if not detail:
        return {
            'status': 'failure',
            'message': 'Detail[{},{}] not found.'.format(government, no)
        }

    result = {
        'status': 'success',
        'detail': detail
    }
    return jsonify(result)
