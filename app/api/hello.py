from flask import jsonify
from flask_restful import Resource
import app.lib.log as log

logger = log.getLogger(__name__)


class Hello(Resource):
    def get(self):
        result = {
            'name': 'Hello'
        }
        return jsonify(result)
