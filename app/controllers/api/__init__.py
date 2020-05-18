from flask import Blueprint
import app.lib.log as log

logger = log.getLogger(__name__)
api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/')
def index():
    return {'message': 'APIs'}
