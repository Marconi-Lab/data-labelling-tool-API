from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy 

from instance.config import app_config

from dotenv import load_dotenv
load_dotenv()

from flask import request, jsonify, abort
# from flask_user import UserManager

db = SQLAlchemy()

def create_app(config_name):
    from application.models import Dataset, User, Item

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # user_manager = UserManager(app, db, User)
    db.init_app(app)

    @app.route('/admin/datasets/', methods=["POST", "GET"])
    def datasets():
        if request.method == "POST":
            name = str(request.data.get("name", ''))
            classes = request.data.getlist("classes")

            if name and classes:
                dataset = Dataset(name=name, classes=classes)
                dataset.save()
                response = jsonify({
                  "id": dataset.id,
                  "name": dataset.name,
                  "classes": dataset.classes,
                  "progress": 0,
                  "date_created": dataset.date_created,
                  "date_modified": dataset.date_modified  
                })
                response.status_code = 201
                return response
        else:
            # GET request
            datasets = Dataset.get_all()
            results = []

            for dataset in datasets:
                #Calculating labelling progress
                labelled_items = Item.query.filter_by(dataset_id=dataset.id).count()
                all_items = Item.query.count()
                if labelled_items and all_items:
                    progress = (labelled_items/all_items)*100
                else: 
                    progress = 0

                obj = {
                    "id": dataset.id,
                    "name": dataset.name,
                    "classes": dataset.classes,
                    "progress": progress,
                    "date_created": dataset.date_created,
                    "date_modified": dataset.date_modified 
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response


    @app.route('/admin/datasets/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def dataset_manipulation(id, **kwargs):

        dataset = Dataset.query.filter_by(id=id).first()

        if not dataset:
            abort(404)

        if request.method == "DELETE":
            dataset.delete()
            return {
                "message": "dataset {} deleted successfully".format(id)
            }, 200
        elif request.method == "PUT":
            name = str(request.data.get("name", ""))
            classes = request.data.getlist("classes")
            dataset.name = name
            dataset.classes = classes
            dataset.save()
            response = jsonify({
                "id": dataset.id,
                "name": dataset.name,
                "classes": dataset.classes,
                "date_created": dataset.date_created,
                "date_modified": dataset.date_modified
            })
            response.status_code = 200
            return response
        else:
            # GET by ID
            labelled_items = Item.query.filter_by(dataset_id=dataset.id).count()
            all_items = Item.query.count()
            if labelled_items and all_items:
                progress = (labelled_items/all_items)*100
            else:
                progress = 0

            response = jsonify({
                "id": dataset.id,
                "name": dataset.name,
                "classes": dataset.classes,
                "progress": progress,
                "date_created": dataset.date_created,
                "date_modified": dataset.date_modified
            })
            response.status_code = 200
            return response
    
    from .auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .admin import admin_blueprint
    app.register_blueprint(admin_blueprint)
    
    from .user import user_blueprint
    app.register_blueprint(user_blueprint)
    return app