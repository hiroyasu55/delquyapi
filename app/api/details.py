from flask import jsonify, request
from flask_restful import Resource
import app.lib.log as log
import app.models.Detail as Detail

logger = log.getLogger(__name__)


class DetailsApi(Resource):
    def get(self, id=None, government=None, no=None):
        result = {}

        if id:
            result = self._find_by_id(id)

        elif government and no:
            result = self._find_by_government_no(government, no)

        else:
            result = self._find(request.args)

        return jsonify(result)

    def _find(self, args):
        filters = []
        offset = args.get('offset', '')
        offset = int(offset) if str.isdecimal(offset) else 0
        limit = args.get('limit', '')
        limit = int(limit) if str.isdecimal(limit) else 50
        if limit > 50:
            limit = 50

        details = Detail.find(filters=filters, offset=offset, limit=limit)
        total = Detail.count(filters=filters)

        result = {
            'status': 'success',
            'details': details,
            'total': total
        }
        return result

    def _find_by_id(self, id):
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
        return result

    def _find_by_government_no(self, government, no):
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
        return result
