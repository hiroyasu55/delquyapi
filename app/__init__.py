# coding:utf-8
from flask import Flask
from flask_cors import CORS
import os
from app.controllers.api import api
from app.controllers.api.persons import api_persons
from app.controllers.api.details import api_details
from app.controllers.api.clusters import api_clusters
from app.controllers.api.summary import api_summary

app = Flask(__name__, instance_relative_config=True)
CORS(app)

app.config.from_object('config')
app.config.from_pyfile('secret.cfg')

app.secret_key = os.urandom(12)

app.register_blueprint(api)
app.register_blueprint(api_persons)
app.register_blueprint(api_details)
app.register_blueprint(api_clusters)
app.register_blueprint(api_summary)


@app.route('/')
def index():
    return 'No contents.'
