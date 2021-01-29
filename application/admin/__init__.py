from flask import Blueprint, request, jsonify, abort
from application.models import Image, Item, User

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
        
    print("+++++++++++item+++++++++++++++++++",item.id)
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