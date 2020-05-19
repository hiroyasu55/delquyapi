from flask import jsonify, request
from flask_restful import Resource
import pandas as pd
import app.lib.log as log
import app.models.Person as Person

logger = log.getLogger(__name__)


class SummaryApi(Resource):
    def get(self, method=None):
        result = {}
        if method == 'count':
            result = self._count(request.args)
        elif method == 'cross':
            result = self._cross(request.args)
        else:
            result = {
                'message': 'No summary method.',
                'status': 'failure',
            }

        return jsonify(result)

    def _count(self, args):
        key = args.get('key')

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
            return result

        sum = df[key].value_counts().to_dict()
        rows = list(map(lambda k: {key: k, 'count': sum[k]}, sum))
        rows = sorted(rows, key=lambda r: r[key])

        result['rows'] = rows

        return result

    def _cross(self, args):
        row_key = args.get('row')
        if not row_key:
            return {
                'status': 'failure',
                'message': 'Parameter "row" not defined.',
            }
        col_key = args.get('col')
        if not col_key:
            return {
                'status': 'failure',
                'message': 'Parameter "col" not defined.',
            }

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
        return result
