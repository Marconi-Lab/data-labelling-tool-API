from flask import Blueprint, request, jsonify, abort
import random

from application.decorators import user_is_authenticated
from application.models import Image, Item, User, Assignment, Dataset, Project, Annotation

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
        project_type = Project.query.filter_by(id=dataset.project_id).first().type

        labelled_images = Image.query.filter_by(dataset_id=assignment.dataset_id, labelled=True, has_box=True,
                                                folder_labelled=True).count()
        all_images = Image.query.filter_by(dataset_id=assignment.dataset_id).count()

        if project_type == "label":
            all_images = Image.query.filter_by(dataset_id=assignment.dataset_id).count()
            labelled_images = Annotation.query.filter_by(user_id=user_id, dataset_id=assignment.dataset_id).count()

        if labelled_images and all_images:
            progress = (labelled_images / all_images) * 100
        else:
            progress = 0
        dataset = {
            "id": dataset.id,
            "name": dataset.name,
            "classes": dataset.classes,
            "progress": progress,
            "project_type": project_type
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
        images = Image.query.filter_by(item_id=item_id)
        for image in images:
            image.folder_labelled = True
            image.save()
        if item.labelled and Image.query.filter_by(item_id=item.id).count() == Image.query.filter_by(item_id=item.id,
                                                                                                     labelled=True,
                                                                                                     folder_labelled=True).count():
            labelled = True
        else:
            labelled = False
        response = jsonify(
            {
                "id": item.id,
                "name": item.name,
                "label": item.label,
                "comment": item.comment,
                "labelled": labelled,
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
        if item.labelled and Image.query.filter_by(item_id=item.id).count() == Image.query.filter_by(item_id=item.id,
                                                                                                     labelled=True,
                                                                                                      folder_labelled=True, has_box=True).count():
            labelled = True
        else:
            labelled = False
        obj = {
            "id": item.id,
            "name": item.name,
            "label": item.label,
            "comment": item.comment,
            "labelled": labelled,
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
    if cervical_area:
        image.has_box = True
    else:
        image.has_box = False
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

# get random unlabelled image
@user_blueprint.route("/user/images/<int:dataset_id>/random", methods=["GET"])
@user_is_authenticated()
def get_random_unlabelled_image(dataset_id):
    user_id = request.headers.get("user_id")
    # all images in dataset
    all_images = Image.query.filter_by(dataset_id=dataset_id).all()
    # this user's annotation record
    labelled_images = Annotation.query.filter_by(user_id=user_id, dataset_id=dataset_id).all()

    progress = f"{len(labelled_images)} labeled out of {len(all_images)}"
    if len(labelled_images) >= len(all_images):
        progress = "done"
    # labelled image ids array
    labelled_image_ids = [i.image_id for i in labelled_images]
    unlabelled_images = list()
    # filter out unlabelled images
    for image in all_images:
        if image.id in labelled_image_ids:
            continue
        unlabelled_images.append(image)
    # Choose random image
    image = random.choice(unlabelled_images)
    project_id = Dataset.query.filter_by(id=image.dataset_id).first().project_id
    response = jsonify({
            "id": image.id,
            "image": image.image_URL,
            "progress": progress,
            "dataset_id": image.dataset_id,
            "project_id": project_id
        })
    response.status_code = 200
    return response

@user_blueprint.route("/user/label/<int:image_id>", methods=["POST"])
@user_is_authenticated()
def label_image(image_id):
    post_data = request.data
    dataset_id = int(request.data.get("dataset_id"))
    project_id = int(request.data.get("project_id"))
    annotations = request.data.get("annotations", "")
    user_id = request.headers.get("user_id")
    image_id = image_id

    annotation = Annotation(dataset_id=dataset_id, project_id=project_id, user_id=user_id, image_id=image_id, annotations=annotations)
    annotation.save()
    response = jsonify({
        "dataset_id": annotation.dataset_id,
        "project_id": annotation.project_id,
        "user_id": annotation.user_id,
        "image_id": annotation.image_id,
        "annotations": annotation.annotations
    })
    response.status_code = 201
    return response