from flask import Blueprint, jsonify, request
import app.lib.log as log
import app.models.Person as Person

logger = log.getLogger(__name__)
api_persons = Blueprint('persons', __name__, url_prefix='/api/persons')


@api_persons.route('', methods=['GET'])
def index():

    filters = []
    if request.args.get('age'):
        filters.append({'key': 'age', 'value': request.args['age']})
    if request.args.get('sex'):
        filters.append({'key': 'sex', 'value': request.args['sex']})
    if request.args.get('area'):
        filters.append({'key': 'area', 'value': request.args['area']})
    if request.args.get('reason'):
        filters.append({'key': 'reason', 'value': request.args['reason']})
    if request.args.get('status'):
        filters.append({'key': 'status', 'value': request.args['status']})
    if request.args.get('release_date'):
        filters.append({'key': 'release_date', 'value': request.args['release_date']})
    else:
        if request.args.get('from_date'):
            filters.append({
                'key': 'release_date', 'symbol': '>=', 'value': request.args['from_date']
            })
        if request.args.get('to_date'):
            filters.append({
                'key': 'release_date', 'symbol': '<=', 'value': request.args['to_date']
            })

    offset = request.args.get('offset', '')
    offset = int(offset) if str.isdecimal(offset) else 0
    limit = request.args.get('limit', '')
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

    return jsonify(result)


@api_persons.route('/<int:no>', methods=['GET'])
def find_by_no(no):
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

    return jsonify(result)


@api_persons.route('/tree', methods=['GET'])
def get_tree():
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


@api_persons.errorhandler(400)
@api_persons.errorhandler(404)
def error_handler_400_404(error):
    return jsonify({
        'status': 'failure',
        'code': error.description['code'],
        'message': error.description['message']
    }), error.code


@api_persons.errorhandler(500)
def error_handler_500(error):
    logger.error(error)
    return jsonify({
        'status': 'failure',
        'code': error.description['code'],
        'message': 'Internal error.'
    }), error.code
