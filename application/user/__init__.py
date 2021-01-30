from flask import Blueprint, request, jsonify, abort
from application.models import Image, Item, User, Assignment, Dataset

user_blueprint = Blueprint('user', __name__)

@user_blueprint.route("/user/<int:user_id>/home/", methods=["GET"])
def get_user_stats(user_id, **kwargs):
    datasets = Assignment.query.filter_by(user_id=user_id).count()
    items = Item.query.filter_by(labelled_by=user_id)
    user = User.query.filter_by(id=user_id).first()
    images_count = 0
    for item in items:
        image_count = Image.query.filter_by(item_id=item.id).count()
        item_count += image_count
    response = jsonify({
        "id": user_id,
        "name": user.username,
        "datasets": datasets,
        "images": images_count
    })
    response.status_code = 200
    return response

@user_blueprint.route("/user/<int:user_id>/datasets/", methods=["GET"])
def get_user_datasets(user_id, *kwargs):
    assignments = Assignment.query.filter_by(user_id=user_id)
    datasets = []
    for assignment in assignments:
        dataset = Dataset.query.filter_by(id=assignment.dataset_id).first()
        dataset = {
            "id": dataset.id,
            "name": dataset.name,
            "classes": dataset.classes
        }
        datasets.append(dataset)
    response = jsonify({
        "id": user_id,
        "datasets": datasets
    })
    response.status_code = 200
    return response

@user_blueprint.route("/user/datasets/item/<int:item_id>/", methods=["GET", "PUT"])
def dataset_items_manipulation(item_id, **kwargs):
    item = Item.query.filter_by(id=item_id).first()
    label = str(request.data.get("label", ""))
    comment = str(request.data.get("comment", ""))
    labeller = str(request.data.get("labeller", ""))

    if request.method == "PUT":
        item.label = label
        item.comment = comment
        item.labelled_by = labeller
        item.labelled = True
        item.save()
        response = jsonify(
            {
            "id": item.id,
            "name": item.name,
            "label": item.label,
            "comment": item.comment,
            "labelled": item.labelled,
            "labelled_by": item.labelled_by
            }
        )
        response.status_code = 200
        return response
    else: 
        images = Image.query.filter_by(item_id=item.id)
        image_URLs = list()
        for image in images:
            image_URLs.append(image.image_URL)

        response = jsonify(
            {
            "id": item.id,
            "name": item.name,
            "label": item.label,
            "comment": item.comment,
            "labelled": item.labelled,
            "labelled_by": item.labelled_by,
            "images": image_URLs
            }
        )
        response.status_code = 200
        return response
@user_blueprint.route("/user/datasets/<int:dataset_id>/", methods=["GET"])
def get_dataset_items(dataset_id):
    dataset = Dataset.query.filter_by(id=dataset_id).first()
    items = Item.query.filter_by(dataset_id=dataset_id)
    data_items = list()

    for item in items:
        obj = {
            "id": item.id,
            "name": item.name,
            "label": item.label,
            "comment": item.comment,
            "labelled": item.labelled,
            "labelled_by": item.labelled_by
        }
        data_items.append(obj)
    response = jsonify({
        "id": dataset.id,
        "name": dataset.name,
        "items": data_items
    })
    response.status_code = 200
    return response