from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy 

from instance.config import app_config

from dotenv import load_dotenv
load_dotenv()

from flask import request, jsonify, abort

db = SQLAlchemy()

def create_app(config_name):
    from application.models import Datasets

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    @app.route('/datasets/', methods=["POST", "GET"])
    def datasets():
        if request.method == "POST":
            name = str(request.data.get("name", ''))
            classes = request.data.getlist("classes")

            if name and classes:
                dataset = Datasets(name=name, classes=classes)
                dataset.save()
                response = jsonify({
                  "id": dataset.id,
                  "name": dataset.name,
                  "classes": dataset.classes,
                  "date_created": dataset.date_created,
                  "date_modified": dataset.date_modified  
                })
                response.status_code = 201
                return response
        else:
            # GET request
            datasets = Datasets.get_all()
            results = []

            for dataset in datasets:
                obj = {
                    "id": dataset.id,
                    "name": dataset.name,
                    "classes": dataset.classes,
                    "date_created": dataset.date_created,
                    "date_modified": dataset.date_modified 
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response
    return app