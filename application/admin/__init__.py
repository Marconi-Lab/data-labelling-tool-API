from flask import Blueprint, request, jsonify, abort
from application.models import Image, Item, User, Assignment

admin_blueprint = Blueprint('admin', __name__)

from . import admin_views

@admin_blueprint.route("/admin/datasets/item/", methods=["GET"])
def item():
    try:
        #GET request
        dataset_id = str(request.data.get("dataset_id", ""))
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
    except Exception as e:
        response  = {
            "Message": str(e)
        }
        print("================================================================")
        print("Response", response)
        print("================================================================")
        return response
    return response

@admin_blueprint.route("/admin/datasets/item/<int:id>/", methods=["GET", "DELETE"])
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
def user_datasets(dataset_id, **kwargs):
    user_id = str(request.data.get("user_id", ""))
    user_assignment = Assignment.query.filter_by(id=dataset_id)

    if not user_assignment:
        abort(404)

    response = jsonify({
        "id": user_assignment.id,
        "user_id": user_id,
        "dataset_id": dataset_id
    })    
    response.status_code = 200
    return response