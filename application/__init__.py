import csv
import os
import pathlib
import zipfile

from dotenv import load_dotenv
from flask_api import FlaskAPI
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from io import StringIO
from flask import stream_with_context
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

from instance.config import app_config

load_dotenv()

from flask import request, jsonify, abort, send_from_directory

# from flask_user import UserManager

db = SQLAlchemy()


def create_app(config_name):
    from application.models import Dataset, User, Item, Image
    from application.decorators import permission_required

    app = FlaskAPI(__name__, instance_relative_config=True)
    CORS(app)
    app.config['CORS_HEADERS'] = ['Content-Type', 'Authorization', 'is_admin']
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # user_manager = UserManager(app, db, User)
    db.init_app(app)

    @app.route('/admin/datasets/', methods=["POST", "GET"])
    @permission_required()
    def datasets():
        if request.method == "POST":
            name = str(request.data.get("name", ''))
            classes = list(request.data.get("classes"))

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
                # Calculating labelling progress

                labelled_images = Image.query.filter_by(dataset_id=dataset.id, labelled=True, has_box=True, folder_labelled=True).count()
                all_images = Image.query.filter_by(dataset_id=dataset.id).count()

                if labelled_images and all_images:
                    progress = (labelled_images/all_images) * 100
                else:
                    progress = 0

                obj = {
                    "id": dataset.id,
                    "name": dataset.name,
                    "classes": dataset.classes,
                    "classes2": dataset.classes2,
                    "progress": progress,
                    "date_created": dataset.date_created,
                    "date_modified": dataset.date_modified
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/admin/datasets/<int:id>/', methods=['GET', 'PUT', 'DELETE'])
    @permission_required()
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
            labelled_images = Image.query.filter_by(labelled=True, has_box=True).count()
            all_images = Image.query.count()
            all_items = Item.query.count()
            if labelled_items and all_items:
                progress = ((labelled_items + labelled_images)/(all_images + all_items)) * 100
            else:
                progress = 0

            response = jsonify({
                "id": dataset.id,
                "name": dataset.name,
                "classes": dataset.classes,
                "classes2": dataset.classes2,
                "progress": progress,
                "date_created": dataset.date_created,
                "date_modified": dataset.date_modified
            })
            response.status_code = 200
            return response

    @app.route('/admin/datasets/<int:id>/classes2/', methods=['PUT'])
    @permission_required()
    def add_image_classes(id):
        dataset = Dataset.query.filter_by(id=id).first()
        classes = list(request.data.get("classes2"))
        dataset.classes2 = classes
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

    @app.route('/admin/datasets/<int:id>/classes/', methods=['PUT'])
    @permission_required()
    def updated_folder_classes(id):
        dataset = Dataset.query.filter_by(id=id).first()
        classes = list(request.data.get("classes"))
        dataset.classes = classes
        dataset.save()
        response = jsonify({
            "id": dataset.id,
            "name": dataset.name,
            "classes": dataset.classes,
            "data_created": dataset.date_created
        })
        response.status_code = 200
        return response
    @app.route('/download/csv/<int:dataset_id>/', methods=["GET"])
    def stream_csv(dataset_id):
        dataset = Dataset.query.filter_by(id=dataset_id).first()
        def generate():
            data = StringIO()
            w = csv.writer(data)
            #writing header
            w.writerow(('image', 'label', 'label 2', "comment", "cervical area"))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

            # write row
            images = Image.query.filter_by(dataset_id=dataset_id).all()
            print("These images   .... ", images)
            for image in images:
                print(image)
                image_label = image.label
                cervical_area = image.cervical_area
                folder_label = Item.query.filter_by(id=image.item_id).first().label
                image_name = image.image_URL.split('/')[-1]
                image_comment = Item.query.filter_by(id=image.item_id).first().comment

                w.writerow([image_name, folder_label, image_label, image_comment, cervical_area])
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)
        # add filename
        headers = Headers()
        headers.set('Content-Disposition', 'attachment', filename=f"{dataset.name}.csv")
        # stream response as data is generated
        return Response(
            stream_with_context(generate()), mimetype="text/csv", headers=headers
        )
    @app.route('/csv/<int:dataset_id>/', methods=["GET"])
    def get_csv(dataset_id):
        working_path = pathlib.Path().absolute()
        dataset = Dataset.query.filter_by(id=dataset_id).first()
        with open("{}\\{}.csv".format(os.path.join(working_path, "application", "static"), dataset.name), "w",
                  newline="") as f:
            # with open(f"{dataset.name}.csv", "w", newline="") as f:
            writer = csv.writer(f)

            writer.writerow(["image", "label_1", "label_2", "comment"])
            print("Dataset id", dataset_id)

            images = Image.query.filter_by(dataset_id=dataset_id).all()
            print("These images   .... ", images)
            for image in images:
                print(image)
                image_label = image.label
                folder_label = Item.query.filter_by(id=image.item_id).first().label
                image_name = image.image_URL.split('/')[-1]
                image_comment = Item.query.filter_by(id=image.item_id).first().comment

                writer.writerow([image_name, folder_label, image_label, image_comment])

        return send_from_directory(directory=os.path.join(working_path, "application", "static"),
                                   filename=f"{dataset.name}.csv", as_attachment=True)
        # return send_from_directory(directory=".", filename=f"{dataset.name}.csv", as_attachement=True)

    @app.route('/download/<int:dataset_id>/', methods=["GET"])
    def download_dataset(dataset_id):
        working_path = pathlib.Path().absolute()
        print("Working path", working_path)
        dataset = Dataset.query.filter_by(id=dataset_id).first()
        with zipfile.ZipFile("{}\\{}.zip".format(os.path.join(working_path, "application", "static"), dataset.name),
                             "w") as dataset_zip:
            for folder_class in dataset.classes:
                print("Current folder", folder_class)
                if dataset.classes2:
                    for i in dataset.classes2:
                        print("Current image class", i)
                        images = Image.query.filter_by(label=i)
                    for image in images:
                        folder = Item.query.filter_by(id=image.item_id).first()
                        print("Folder label", folder.label)
                        print("Folder class", folder_class)
                        if folder.label == folder_class:
                            image_name = image.image_URL.split("/")[-1]
                            print("Current image", image_name)
                            dataset_zip.write(os.path.join(working_path, "application", "static", image_name),
                                              "{}\\{}\\{}".format(folder_class, i, image_name),
                                              zipfile.ZIP_DEFLATED)
        return send_from_directory(directory=os.path.join(working_path, "application", "static"),
                                   filename=f"{dataset.name}.zip", as_attachment=True)

    from .auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .admin import admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .user import user_blueprint
    app.register_blueprint(user_blueprint)
    return app
