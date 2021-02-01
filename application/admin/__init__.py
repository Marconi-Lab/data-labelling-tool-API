from flask import Blueprint, request, jsonify, abort, url_for
from application.models import Image, Item, User, Assignment, Dataset
from application.decorators import permission_required
from werkzeug.utils import secure_filename
import os
import application as app

from dotenv import load_dotenv
load_dotenv()

admin_blueprint = Blueprint('admin', __name__)

@admin_blueprint.route("/admin/datasets/item/", methods=["GET", "POST"])
@permission_required()
def item():
    try:
        #GET request
        dataset_id = str(request.data.get("dataset_id", ""))
        if request.method == "GET":
            items = Item.get_all(dataset_id)
            results = []

            for item in items:
                images = Image.get_all(item.id)
                image_URLs = [i.image_URL for i in images]
                obj = {
                    "dataset_id": dataset_id,
                    "id": item.id,
                    "name": item.name,
                    "images_URLs": image_URLs,
                    "label": item.label,
                    "comment": item.comment,
                    "labelled": item.labelled
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response
        else:
            #  POST Request
            name = str(request.data.get("name", ''))

            if name:
                item = Item(name=name, dataset_id=dataset_id)
                item.save()
                response = jsonify({
                    "id": item.id,
                    "name": item.name,
                    "dataset_id": dataset_id,
                    "Message": "Item was successfully added"
                })
                response.status_code = 201
                return response
    except Exception as e:
        response  = {
            "Message": str(e)
        }
        print("================================================================")
        print("Response", response)
        print("================================================================")
        return response


@admin_blueprint.route("/admin/datasets/item/<int:id>/", methods=["GET", "DELETE"])
@permission_required()
def item_manipulation(id, **kwargs):

    dataset_id = str(request.data.get("dataset_id", ""))
    item = Item.query.filter_by(id=id).first()
    if not item:
        abort(404)

    images = Image.get_all(item.id)
    image_URLs = [i.image_URL for i in images]


    if request.method == "DELETE":
        item.delete()
        return{
            "message": "Item {} deleted successfully".format(id)
        }, 200
    else:
        # GET by ID
        response = jsonify({
            "dataset_id": dataset_id,
            "id": item.id,
            "name": item.name,
            "images_URLs": image_URLs,
            "label": item.label,
            "comment": item.comment,
            "labelled": item.labelled
        })
        response.status_code = 200
        return response

@admin_blueprint.route("/admin/users/", methods=["GET"])
@permission_required()
def user():
    #GET request
    users = User.get_all()
    results = []

    for user in users:
        obj = {
            "id": user.id,
            "username": user.username
        }
        results.append(obj)
    response = jsonify(results)
    response.status_code = 200
    return response

@admin_blueprint.route("/admin/users/datasets/<int:dataset_id>/", methods=["GET"])
@permission_required()
def user_datasets(dataset_id, **kwargs):
    user_id = str(request.data.get("user_id", ""))
    user_assignment = Assignment.query.filter_by(dataset_id=int(dataset_id), user_id=int(user_id)).first()

    if not user_assignment:
        abort(404)

    response = jsonify({
        "id": user_assignment.id,
        "user_id": user_id,
        "dataset_id": dataset_id
    })    
    response.status_code = 200
    return response

@admin_blueprint.route("/admin/users/<int:user_id>/assignments/", methods=["POST", "GET", "DELETE"])
@permission_required()
def user_assignments_manipulation(user_id, **kwargs):
    # assigment = Assignment.query.filter_by()
    if request.method == "POST":
        dataset_id = str(request.data.get("dataset_id", ""))
        dataset = Dataset.query.filter_by(id=int(dataset_id)).first()
        if not dataset:
            abort(404)
        assignment = Assignment(user_id=int(user_id), dataset_id=int(dataset_id))
        assignment.save()
        response = jsonify({
            "id": assignment.id,
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "classes": dataset.classes,
            },
            "user_id": user_id
        })
        response.status_code = 201
        return response
    elif request.method == "DELETE":
        dataset_id = str(request.data.get("dataset_id", ""))
        dataset = Dataset.query.filter_by(id=int(dataset_id)).first()
        if not dataset:
            abort(404)
        assignment = Assignment.query.filter_by(user_id=int(user_id), dataset_id=int(dataset_id)).first()
        assignment.delete()
        return {
            "Message": "Assignment {} deleted successfully".format(id)
        }, 200
    else:
        # GET Request
        assignments = Assignment.get_user_datasets(user_id)
        results = []
        for i in assignments:
            dataset = Dataset.query.filter_by(id=i.dataset_id).first()
            obj = {
                "id": i.id,
                "dataset": {
                    "id": dataset.id,
                    "name": dataset.name,
                    "classes": dataset.classes,
                },
                "user_id": i.user_id
            }
            results.append(obj)
        response = jsonify(results)
        response.status_code = 200
        return response

@admin_blueprint.route('/admin/<int:id>/home/', methods=["GET"])
@permission_required()
def admin_stats(id, **kwargs):
    admin = User.query.filter_by(id=id).first()
    users = User.count_all()
    datasets = Dataset.count_all()
    response = jsonify({
        "id": admin.id,
        "name": admin.username,
        "users": users,
        "datasets": datasets
    })
    response.status_code = 200
    return response

allowed_extensions = set(['image/jpeg', 'image/png', 'jpeg'])
uploads_dir = os.path.join(os.path.dirname(app.__file__), os.environ.get("UPLOAD_FOLDER"))

def allowed_file(filename):
    return filename in allowed_extensions


@admin_blueprint.route("/admin/item/<int:item_id>/", methods=["POST"])
def upload_images(item_id):
    try:
        images_list = request.files.getlist("images")

        images = list()
        for image in images_list:
            if image and allowed_file(image.content_type):
                image_name = secure_filename(image.filename)
                image.save(os.path.join(uploads_dir, image_name))
                image_url = url_for(os.environ.get("UPLOAD_FOLDER"), filename=image_name, _external=True)
                image_upload = Image(name=image_name, image_URL=image_url)
                image_upload.item_id = item_id
                image_upload.save()
                obj = {
                    "id": image_upload.id,
                    "image": image_url
                }
                images.append(obj)
        response = jsonify({
            "message": "Images were successfully added",
            "item_id": item_id,
            "images": images
        })
        response.status_code = 201
        return response
    except Exception as e:
        response = jsonify({
            "message": str(e)
        })
        response.status_code = 500
        print("Message: ", e)
        return response

@admin_blueprint.route("/admin/datasets/images/", methods=["POST"])
def dataset_image_upload():
    try:
        image = request.files["image"]
        dataset_id = str(request.data.get("dataset_id", ""))
        if image and allowed_file(image.content_type):
            image_name = secure_filename(image.filename)
            image.save(os.path.join(uploads_dir, image_name))
            image_url = url_for(os.environ.get("UPLOAD_FOLDER"), filename=image_name, _external=True)
            image_upload = Image(name=image_name, image_URL=image_url)
            image_upload.dataset_id = dataset_id
            image_upload.save()
        response = jsonify({
            "message": "Image was successfully added",
            "dataset_id": dataset_id,
            "image": image_url,
            "id": image_upload.id
        })
        response.status_code = 201
        return response
    except Exception as e:
        response = jsonify({
            "message": str(e)
        })
        response.status_code = 500
        print("Message: ", e)
        return response