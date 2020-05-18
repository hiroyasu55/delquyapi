from flask import Blueprint, jsonify, request
import pandas as pd
import app.lib.log as log
import app.models.Person as Person

logger = log.getLogger(__name__)
api_summary = Blueprint('summary', __name__, url_prefix='/api/summary')


@api_summary.route('/', methods=['GET'])
def index():
    result = {
        'status': 'success',
    }
    return jsonify(result)


@api_summary.route('/count', methods=['GET'])
def count():
    key = request.args.get('key')

    persons = Person.find()
    total = len(persons)

    df = pd.DataFrame(persons)
    current_date = df['release_date'].max()

    result = {
        'status': 'success',
        'current_date': current_date,
        'total': total
    }

    if not key:
        return jsonify(result)
    sum = df[key].value_counts().to_dict()
    rows = list(map(lambda k: {key: k, 'count': sum[k]}, sum))
    rows = sorted(rows, key=lambda r: r[key])

    result['rows'] = rows

    return jsonify(result)


@api_summary.route('/cross', methods=['GET'])
def cross():
    row_key = request.args.get('row')
    if not row_key:
        return jsonify({
            'status': 'failure',
            'message': 'Parameter "row" not defined.',
        })
    col_key = request.args.get('col')
    if not col_key:
        return jsonify({
            'status': 'failure',
            'message': 'Parameter "col" not defined.',
        })

    persons = Person.find()
    total = len(persons)
    df = pd.DataFrame(persons)
    current_date = df['release_date'].max()

    row_total = df[row_key].value_counts().to_dict()

    table = pd.crosstab(df[col_key], df[row_key])
    data = table.to_dict()
    rows = []
    for key in data:
        row = {
            row_key: key,
            'values': list(map(lambda name: {'name': name, 'count': data[key][name]}, data[key])),
            'total': row_total.get(key) or 0
        }
        rows.append(row)

    col_total = df[col_key].value_counts().to_dict()
    col_total = list(map(lambda name: {'name': name, 'count': col_total[name]}, col_total))

    result = {
        'status': 'success',
        'current_date': current_date,
        'rows': rows,
        'col_total': col_total,
        'total': total
    }
    return jsonify(result)


@api_summary.errorhandler(400)
@api_summary.errorhandler(404)
def error_400_404(error):
    return jsonify({
        'status': 'failure',
        'code': error.description['code'],
        'message': error.description['message']
    }), error.code


@api_summary.errorhandler(500)
def error_500(error):
    return jsonify({
        'status': 'failure',
        'code': error.description['code'],
        'message': 'Internal error.'
    }), error.code
