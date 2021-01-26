from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy 

from instance.config import app_config

from dotenv import load_dotenv
load_dotenv()

from flask import request, jsonify, abort

db = SQLAlchemy()

def create_app(config_name):
    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    @app.route('/datasets/', methods=["POST", "GET"])
    def bucketlists():
        if request.method == "POST":
            data = request.data
            if data.name and data.classes:
                dataset = Dataset(name=data.name, classes=data.classes)
                dataset.save()
                response = jsonify({
                  "id": dataset.id,
                  "name": dataset.name,
                  "classes": dataset.classes
                  "date_created": dataset.date_created,
                  "date_modified": dataset.date_modified  
                })
                resoponse.status_code = 201
                return response
        else:
    return app