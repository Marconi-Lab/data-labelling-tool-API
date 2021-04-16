from flask import Blueprint, request, jsonify, abort

from application.decorators import user_is_authenticated
from application.models import Image, Item, User, Assignment, Dataset

user_blueprint = Blueprint('user', __name__)


@user_blueprint.route("/user/<int:user_id>/home/", methods=["GET"])
@user_is_authenticated()
def get_user_stats(user_id, **kwargs):
    datasets = Assignment.query.filter_by(user_id=user_id).count()
    items = Item.query.filter_by(labelled_by=user_id)
    user = User.query.filter_by(id=user_id).first()
    if not user:
        abort(404)
    images_count = 0
    for item in items:
        image_count = Image.query.filter_by(item_id=item.id).count()
        images_count += image_count
    response = jsonify({
        "id": user_id,
        "name": user.username,
        "datasets": datasets,
        "images": images_count
    })
    response.status_code = 200
    return response


@user_blueprint.route("/user/<int:user_id>/datasets/", methods=["GET"])
@user_is_authenticated()
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


@user_blueprint.route("/user/item/<int:item_id>/", methods=["GET", "PUT"])
@user_is_authenticated()
def dataset_items_manipulation(item_id, **kwargs):
    item = Item.query.filter_by(id=item_id).first()
    dataset = Dataset.query.filter_by(id=item.dataset_id).first()
    if not item:
        abort(404)
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
        images = images.order_by(Image.id.asc())
        image_URLs = list()
        for image in images:
            image_URLs.append(
                {"id": image.id, "image": image.image_URL, "labelled": image.labelled, "label": image.label,
                 "bounding_box": image.cervical_area})

        response = jsonify(
            {
                "id": item.id,
                "name": item.name,
                "label": item.label,
                "comment": item.comment,
                "labelled": item.labelled,
                "labelled_by": item.labelled_by,
                "images": image_URLs,
                "image_classes": dataset.classes2,
                "dataset_id": dataset.id,
                "dataset_classes": dataset.classes
            }
        )
        response.status_code = 200
        return response


@user_blueprint.route("/user/datasets/<int:dataset_id>/", methods=["GET"])
@user_is_authenticated()
def get_dataset_items(dataset_id):
    dataset = Dataset.query.filter_by(id=dataset_id).first()
    if not dataset:
        abort(404)
    items = Item.query.filter_by(dataset_id=dataset_id).order_by(Item.name)
    if not items:
        abort(404)
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


@user_blueprint.route("/user/images/<int:image_id>/", methods=["GET", "PUT"])
@user_is_authenticated()
def manipulate_images(image_id):
    if request.method == "GET":
        image = Image.query.filter_by(id=image_id).first()
        if not image:
            abort(404)
        response = jsonify({
            "id": image.id,
            "image": image.image_URL,
            "label": image.label,
            "labelled": image.labelled,
            "labelled_by": image.labelled_by,
            "dataset_id": image.dataset_id,
            "item_id": image.item_id,
            "bounding_box": image.cervical_area
        })
        response.status_code = 200
        return response
    else:
        # PUT Request
        label = request.data.get("label", "")
        labeller = request.data.get("labeller", "")
        image = Image.query.filter_by(id=image_id).first()
        image.label = label
        image.labelled_by = labeller
        image.labelled = True
        image.save()
        response = jsonify(
            {
                "id": image.id,
                "label": image.label,
                "labelled": image.labelled,
                "labelled_by": image.labelled_by
            }
        )
        response.status_code = 200
        return response


@user_blueprint.route("/user/images/boundingbox/<int:image_id>/", methods=["PUT"])
@user_is_authenticated()
def add_bounding_box(image_id):
    cervical_area = request.data.get("bounding_box", "")
    image = Image.query.filter_by(id=image_id).first()
    image.cervical_area = cervical_area
    image.save()
    response = jsonify({
        "id": image.id,
        "label": image.label,
        "labelled": image.labelled,
        "labelled_by": image.labelled_by,
        "cervical_area": image.cervical_area
    })
    response.status_code = 200
    return response
