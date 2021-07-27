import io
import os
import csv
import json

from PIL import Image as Img
import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, abort, url_for, stream_with_context
from werkzeug.utils import secure_filename

from io import StringIO
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

import application as app
from application.decorators import permission_required
from application.models import Image, Item, User, Assignment, Dataset

load_dotenv()

admin_blueprint = Blueprint('admin', __name__)


@admin_blueprint.route('/admin/datasets/', methods=["POST", "GET"])
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

            labelled_images = Image.query.filter_by(dataset_id=dataset.id, labelled=True, has_box=True,
                                                    folder_labelled=True).count()
            all_images = Image.query.filter_by(dataset_id=dataset.id).count()

            if labelled_images and all_images:
                progress = (labelled_images / all_images) * 100
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


@admin_blueprint.route('/admin/datasets/<int:id>/', methods=['GET', 'PUT', 'DELETE'])
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
            progress = ((labelled_items + labelled_images) / (all_images + all_items)) * 100
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


@admin_blueprint.route('/admin/datasets/<int:id>/classes2/', methods=['PUT'])
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


@admin_blueprint.route('/admin/datasets/<int:id>/classes/', methods=['PUT'])
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


@admin_blueprint.route('/download/csv/<int:dataset_id>/', methods=["GET"])
def stream_csv(dataset_id):
    dataset = Dataset.query.filter_by(id=dataset_id).first()

    def generate():
        data = StringIO()
        w = csv.writer(data)
        # writing header
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


@admin_blueprint.route("/admin/download/object_detection", methods=["GET"])
def object_detection_dataset():
    try:
        print(request.data)
        users = request.args.getlist("users[]")
        print("Users ids: ", users)

        def generate():
            data = StringIO()
            w = csv.writer(data)
            # writing header
            w.writerow(('image', 'label', 'label 2', "comment", "cervical area"))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

            # write row
            for user_id in users:
                print(user_id)
                images = Image.query.filter_by(labelled_by=user_id).all()
                user = User.query.filter_by(id=user_id).first()
                print("These images   .... ", images)
                for image in images:
                    print(image)
                    dataset = Dataset.query.filter_by(id=image.dataset_id).first()
                    if not "cvc" in dataset.name:
                        image_label = image.label
                        cervical_area = image.cervical_area
                        folder_label = Item.query.filter_by(id=image.item_id).first().label
                        image_name_values = image.image_URL.split('/')[-1].split("_")
                        image_name = user.username + "_" + image_name_values[-2] + "_" + image_name_values[-1]
                        image_comment = Item.query.filter_by(id=image.item_id).first().comment

                        w.writerow([image_name, folder_label, image_label, image_comment, cervical_area])
                        yield data.getvalue()
                        data.seek(0)
                        data.truncate(0)

        # add filename
        headers = Headers()
        headers.set('Content-Disposition', 'attachment', filename=f"object_detection_dataset.csv")
        # stream response as data is generated
        return Response(
            stream_with_context(generate()), mimetype="text/csv", headers=headers
        )
    except Exception as e:
        response = jsonify({"message": str(e)})
        print(response)
        return response


@admin_blueprint.route("/admin/download/by_case", methods=["GET"])
def ordered_by_case_dataset():
    try:
        cases = Item.query.all()
        case_ids = list(set([i.name for i in cases]))
        case_ids.sort()
        data = {"Case": case_ids, "Nurse1_case_diagnosis": ["-" for i in case_ids],
                "Nurse2_case_diagnosis": ["-" for i in case_ids],
                "Jane_case_diagnosis": ["-" for i in case_ids],
                "Nurse1_bounding_boxes": ["-" for i in case_ids], "Nurse2_bounding_boxes": ["-" for i in case_ids],
                "Jane_bounding_boxes": ["-" for i in case_ids], "Label 2": ["-" for i in case_ids]}
        df = pd.DataFrame.from_dict(data)
        df.set_index("Case", inplace=True)
        print(df)
        users = request.args.getlist("users[]")
        # write row
        for user_id in users:
            print(user_id)
            items = Item.query.filter_by(labelled_by=user_id).all()
            print("Here goes items ", items)
            usr = User.query.filter_by(id=user_id).first()

            for itm in list(items):
                print(itm.label)
                dataset = Dataset.query.filter_by(id=itm.dataset_id).first()
                images = Image.query.filter_by(item_id=itm.id).all()
                #print("Image 1 label: ", images[0].label)
                bounding_boxes = str([i.cervical_area for i in images])
                label_2 = str([i.label for i in images])
                if str(usr.username) == "Jane":
                    df.loc[str(itm.name),"Jane_case_diagnosis"] = itm.label
                    df.loc[str(itm.name), "Jane_bounding_boxes"] = bounding_boxes
                    df.loc[str(itm.name),"Label 2"] = label_2
                else:
                    if not "cvc" in dataset.name:
                        # image_label = image.label
                        df.loc[str(itm.name),"Nurse1_case_diagnosis"] = itm.label
                        df.loc[str(itm.name),"Nurse1_bounding_boxes"] = bounding_boxes
                        if usr.username == 'AvakoFlorence':
                            df.loc[str(itm.name), "Nurse2_case_diagnosis"] = itm.label
                            df.loc[str(itm.name), "Nurse2_bounding_boxes"] = bounding_boxes
                    else:
                        df.loc[str(itm.name),"Nurse2_case_diagnosis"] = itm.label
                        df.loc[str(itm.name),"Nurse2_bounding_boxes"] = bounding_boxes
        df.fillna("")
        # add filename
        headers = Headers()
        headers.set('Content-Disposition', 'attachment', filename=f"ordered_by_case.csv")
        # stream response as data is generated
        return Response(
            stream_with_context(df.to_csv(chunksize=100)), mimetype="text/csv", headers=headers
        )
    except Exception as e:
        raise e
        response = jsonify({"message": str(e)})
        print(response)
        return response


@admin_blueprint.route("/admin/<int:dataset_id>/item/", methods=["GET", "POST"])
@permission_required()
def item(dataset_id):
    try:
        # GET request
        if request.method == "GET":
            items = Item.get_all(dataset_id)
            results = []

            for item in items:
                if item.labelled and Image.query.filter_by(item_id=item.id).count() == Image.query.filter_by(
                        item_id=item.id,
                        labelled=True,
                        folder_labelled=True, has_box=True).count():
                    labelled = True
                else:
                    labelled = False
                images = Image.get_all(item.id)
                image_URLs = [i.image_URL for i in images]
                obj = {
                    "dataset_id": dataset_id,
                    "id": item.id,
                    "name": item.name,
                    "images_URLs": image_URLs,
                    "label": item.label,
                    "comment": item.comment,
                    "labelled": labelled
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
        response = {
            "Message": str(e)
        }
        print("================================================================")
        print("Response", response)
        print("================================================================")
        return response


@admin_blueprint.route("/admin/item/<int:id>/", methods=["GET", "DELETE"])
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
        return {
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
    # GET request
    users = User.query.filter_by(is_admin="")
    results = []

    for user in users:
        assignments = Assignment.query.filter_by(user_id=user.id)
        dataset_count = assignments.count()
        record_count = Image.query.filter_by(labelled_by=user.id).count()
        datasets = list()
        for assignment in assignments:
            dataset = Dataset.query.filter_by(id=assignment.dataset_id).first()
            dataset = {
                "id": dataset.id,
                "name": dataset.name
            }
            datasets.append(dataset)
        obj = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "dataset_count": dataset_count,
            "datasets": datasets,
            "record_count": record_count
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


@admin_blueprint.route("/admin/users/<int:user_id>/assignments/", methods=["POST", "GET"])
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


@admin_blueprint.route("/admin/users/<int:user_id>/assignments/<int:dataset_id>/", methods=["DELETE"])
@permission_required()
def delete_assignment(user_id, dataset_id):
    dataset = Dataset.query.filter_by(id=dataset_id).first()
    if not dataset:
        abort(404)
    assignment = Assignment.query.filter_by(user_id=int(user_id), dataset_id=int(dataset_id)).first()
    assignment.delete()
    return {
               "Message": "Assignment {} deleted successfully".format(id)
           }, 200


@admin_blueprint.route('/admin/<int:id>/home/', methods=["GET"])
@permission_required()
def admin_stats(id, **kwargs):
    admin = User.query.filter_by(id=id).first()
    users = User.query.filter_by(is_admin="").count()
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
        print(request.files.getlist("images"))
        images_list = request.files.getlist("images")
        dataset_id = Item.query.filter_by(id=item_id).first().dataset_id
        images = list()
        for image in images_list:
            print(image)
            if image and allowed_file(image.content_type):
                image_name = secure_filename(image.filename)
                image = Img.open(io.BytesIO(image.stream.read()))
                #                 image = image.resize((1024, 1024), Img.ANTIALIAS)
                image.save(os.path.join(uploads_dir, image_name))
                image_url = url_for(os.environ.get("UPLOAD_FOLDER"), filename=image_name, _external=True)
                image_upload = Image(name=image_name, image_URL=image_url)
                image_upload.item_id = item_id
                image_upload.dataset_id = dataset_id
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


@admin_blueprint.route("/admin/<int:dataset_id>/bulk_upload/", methods=["POST"])
def dataset_bulk_upload(dataset_id):
    try:
        # retrieve image and path
        images = request.files.getlist("images")
        paths = request.form.getlist("details")
        # initalize images list
        imgs = list()
        for i, image in enumerate(images):
            # get folder name
            folder_name = paths[i].split("/")[1]
            print("Folder_name ", folder_name)
            # Get folder
            folder = Item.query.filter_by(name=folder_name).first()
            print("Folder", folder)
            if not folder:
                # create new folder if not already existing
                folder = Item(name=folder_name, dataset_id=dataset_id)
                folder.save()
                print(folder)
            # Do this if image is of allowed type
            if image and allowed_file(image.content_type):
                image_name = folder_name + paths[i].split("/")[2]
                # read image
                image = Img.open(io.BytesIO(image.stream.read()))
                image.save(os.path.join(uploads_dir, image_name))
                image_url = url_for(os.environ.get("UPLOAD_FOLDER"), filename=image_name, _external=True)
                image_upload = Image(name=image_name, image_URL=image_url)
                image_upload.item_id = folder.id
                image_upload.dataset_id = dataset_id
                image_upload.save()
                print("Uploaded ", image_name)
                obj = {
                    "id": image_upload.id,
                    "image": image_url
                }
                imgs.append(obj)
        response = jsonify({
            "message": "Successfully uploaded dataset",
            "images": imgs,
            "id": dataset_id
        })
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
        # print(request.files)
        image = request.files["image"]
        dataset_id = str(request.data.get("dataset_id", ""))
        folder_name = str(request.data.get("folder", ""))
        # print("image ", image)
        # print("dataset_id", dataset_id)
        # print("folder", folder_name)
        # get folder
        folder = Item.query.filter_by(name=folder_name, dataset_id=dataset_id).first()
        # print("Folder", folder)
        if not folder:
            # create new folder if not already existing
            folder = Item(name=folder_name, dataset_id=dataset_id)
            folder.save()
            print("Folder ", folder)
        if image and allowed_file(image.content_type):
            image_name = secure_filename(image.filename)
            image.save(os.path.join(uploads_dir, image_name))
            image_url = url_for(os.environ.get("UPLOAD_FOLDER"), filename=image_name, _external=True)
            image_upload = Image(name=image_name, image_URL=image_url)
            image_upload.dataset_id = dataset_id
            image_upload.item_id = folder.id
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


@admin_blueprint.route("/admin/images/<int:image_id>/", methods=["DELETE"])
def delete_image(image_id):
    image = Image.query.filter_by(id=image_id).first()
    image.delete()
    response = jsonify({
        "Message": "Image {} successfully deleted".format(image_id)
    })
    response.status_code = 200
    return response
