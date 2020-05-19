from flask import jsonify, request
from flask_restful import Resource
import app.lib.log as log
import app.models.Person as Person

logger = log.getLogger(__name__)


class PersonsApi(Resource):
    def get(self, no=None):
        result = {}
        if no:
            result = self._find_by_no(no)
        else:
            result = self._find(request.args)

        return jsonify(result)

    def _find(self, args={}):
        filters = []
        if args.get('age'):
            filters.append({'key': 'age', 'value': request.args['age']})
        if args.get('sex'):
            filters.append({'key': 'sex', 'value': request.args['sex']})
        if args.get('area'):
            filters.append({'key': 'area', 'value': request.args['area']})
        if args.get('reason'):
            filters.append({'key': 'reason', 'value': request.args['reason']})
        if args.get('status'):
            filters.append({'key': 'status', 'value': request.args['status']})
        if args.get('cluster_no'):
            filters.append({'key': 'cluster_no', 'value': int(request.args['cluster_no'])})
        if args.get('release_date'):
            filters.append({'key': 'release_date', 'value': request.args['release_date']})
        else:
            if args.get('from_date'):
                filters.append({
                    'key': 'release_date', 'symbol': '>=', 'value': request.args['from_date']
                })
            if args.get('to_date'):
                filters.append({
                    'key': 'release_date', 'symbol': '<=', 'value': request.args['to_date']
                })

        offset = args.get('offset', '')
        offset = int(offset) if str.isdecimal(offset) else 0
        limit = args.get('limit', '')
        limit = int(limit) if str.isdecimal(limit) else None

        persons = Person.find(filters=filters, offset=offset, limit=limit)
        total = Person.count(filters=filters)
        current_date = Person.current_date()

        result = {
            'status': 'success',
            'current_date': current_date,
            'persons': persons,
            'total': total
        }

        return result

    def _find_by_no(self, no):
        person = Person.find_by_no(no)
        if not person:
            return {
                'status': 'failure',
                'reason': 'Person not found.'
            }

        result = {
            'status': 'success',
            'person': person
        }

        return result


class TreeApi(Resource):
    def get(self):
        person = None

        if request.args.get('no'):
            no = int(request.args['no'])
            person = Person.find_by_no(no)
            if not person:
                return {
                    'status': 'failure',
                    'reason': 'Person not found.'
                }

        tree = Person.get_tree(person=person)
        result = {
            'status': 'success',
            'tree': tree
        }

        return jsonify(result)
