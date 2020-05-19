from flask import Flask, jsonify
from flask_cors import CORS
import os
import app.lib.log as log
import app.api as api

logger = log.getLogger(__name__)

app = Flask(__name__, instance_relative_config=True)
CORS(app)
app.config.from_object('config')
app.config.from_pyfile('secret.cfg')
app.secret_key = os.urandom(12)

app.register_blueprint(api.app)


@app.errorhandler(400)
@app.errorhandler(404)
def error_handler_400_404(error):
    return jsonify({
        'status': 'failure',
        'code': error.code,
        'message': error.name
    }), error.code


@app.errorhandler(500)
def error_handler_500(error):
    logger.error(error)
    return jsonify({
        'status': 'failure',
        'code': error.code,
        'message': error.name
    }), error.code
