from flask import Blueprint
from flask_restful import Api
import app.lib.log as log
from app.api.hello import Hello
from app.api.persons import PersonsApi, TreeApi
from app.api.details import DetailsApi
from app.api.clusters import ClustersApi
from app.api.summary import SummaryApi

logger = log.getLogger(__name__)

app = Blueprint('api', __name__, url_prefix='/api')
api = Api(app)

api.add_resource(Hello, '/hello')
api.add_resource(PersonsApi, '/persons', '/persons/<int:no>')
api.add_resource(TreeApi, '/persons/tree')
api.add_resource(DetailsApi, '/details', '/details/<id>', '/details/<government>/<int:no>')
api.add_resource(ClustersApi, '/clusters', '/clusters/<int:no>')
api.add_resource(SummaryApi, '/summary/<method>')
