from flask import Flask, jsonify
from flask_cors import CORS
import os
import app.lib.log as log
import app.api as api
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp
from app.models.User import User


logger = log.getLogger(__name__)

# _users = [
#     User(1, 'user1', 'abcxyz'),
#     User(2, 'user2', 'abcxyz'),
# ]
# userid_table = {u.id: u for u in _users}
# username_table = {u.name: u for u in _users}
# print(_users[0])


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__, instance_relative_config=True)
CORS(app)
app.config.from_object('config')
app.config.from_pyfile('secret.cfg')
app.secret_key = os.urandom(12)

app.register_blueprint(api.app)
# jwt = JWT(app, authenticate, identity)


# @app.route('/protected')
# @jwt_required()
# def protected():
#     return '%s' % current_identity


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
