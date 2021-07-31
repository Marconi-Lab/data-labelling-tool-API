import os
import requests
from PIL import Image as Img
import uuid

from flask import request, Blueprint, jsonify, url_for
from werkzeug.utils import secure_filename

from flask import current_app as app
from application.models import Image, Item, Dataset
from ..admin import allowed_file

from .predict import predict_url, initialize

external_blueprint = Blueprint("external", __name__)

uploads_dir = app.config["EXTERNAL_UPLOADS"]
resized_uploads_dir = os.path.join(app.config["EXTERNAL_UPLOADS"], "resized")


def create_image(picture, folder_name, folder_id, dataset_id, image_label, picture_key, pos_thres):
    try:
        image = Img.open(requests.get(picture, stream=True).raw)
    except Exception as e:
        return f"Error downloading {picture_key}"
    else:
        if allowed_file(image.get_format_mimetype()):
            prediction = predict_url(picture, pos_thres)["predictions"]

            print(image.get_format_mimetype(), "  image name ", image.filename)
            image_name = secure_filename(folder_name + "-" + str(uuid.uuid4()) + ".jpg")
            print("Image name ", image_name)
            image_resized = image.resize((512, 512), Img.ANTIALIAS)
            # save original
            image.save(os.path.join(uploads_dir, image_name))
            print("saved image")
            # save resized
            image_resized.save(os.path.join(resized_uploads_dir, image_name))

            image_url = url_for(os.environ.get("UPLOAD_FOLDER"), filename=f"external/resized/{image_name}",
                                _external=True)
            print("image_url: ", image_url)
            image_upload = Image(name=image_name, image_URL=image_url)
            print("Created image upload")
            image_upload.item_id = folder_id
            image_upload.dataset_id = dataset_id
            image_upload.label = image_label
            image_upload.labelled = True
            image_upload.save()
            print("Concluded image upload")
    return (picture, prediction)


@external_blueprint.route("/upload", methods=["POST"])
def upload_data():
    try:
        initialize()
        payload = request.get_json()
        print("Payload ", payload["picture1_before"])
        #  check if dataset exists if not create it
        datasets = Dataset.query.filter_by(name="orchestra_data").all()
        print("datasets ", datasets)
        if len(datasets) > 0:
            dataset = datasets[0]
        else:
            dataset = Dataset(name="orchestra_data",
                              classes=["VIA Positive", "VIA Negative", "Suspicious of cancer", "Other lesions",
                                       "Bad quality images"])
            dataset.save()
        #  create item
        assert payload["study_id"], "No study id found"
        folder = Item(name=payload["study_id"], dataset_id=dataset.id)
        folder.save()

        predicted_classes = list()
        #  create image_1
        try:
            if int(payload["picture1_before"]["acetic_acid"]):
                image1_label = "Stained with acetic acid"
            else:
                image1_label = "Not stained with acetic acid"
            image1_url, pred1 = create_image(payload["picture1_before"]["request_image_url"], folder.name, folder.id,
                                             dataset.id, image1_label, "picture1_before", payload["positive_threshold"])
            predicted_classes.append(pred1["class"])
        except ValueError:
            return jsonify({
                "Message": f"Could not download picture1_before: {payload['picture1_before']['request_image_url']}"
            }), 400
        #  create image_2
        try:
            if int(payload["picture2_before"]["acetic_acid"]):
                image2_label = "Stained with acetic acid"
            else:
                image2_label = "Not stained with acetic acid"
            image2_url, pred2 = create_image(payload["picture2_before"]["request_image_url"], folder.name, folder.id,
                                             dataset.id, image2_label, "picture2_before", payload["positive_threshold"])
            predicted_classes.append(pred2["class"])
        except ValueError:
            return jsonify({
                "Message": f"Could not download picture2_before: {payload['picture2_before']['request_image_url']}"
            }), 400
        #  create image_3
        try:
            if int(payload["picture3_after"]["acetic_acid"]):
                image3_label = "Stained with acetic acid"
            else:
                image3_label = "Not stained with acetic acid"

            image3_url, pred3 = create_image(payload["picture3_after"]["request_image_url"], folder.name, folder.id,
                                             dataset.id, image3_label, "picture3_after", payload["positive_threshold"])
            predicted_classes.append(pred3["class"])
        except ValueError:
            return jsonify({
                "Message": f"Could not download picture3_after: {payload['picture3_after']['request_image_url']}"
            }), 400

        #  create image_4
        try:
            if int(payload["picture4_after"]["acetic_acid"]):
                image4_label = "Stained with acetic acid"
            else:
                image4_label = "Not stained with acetic acid"

            image4_url, pred4 = create_image(payload["picture4_after"]["request_image_url"], folder.name, folder.id,
                                             dataset.id, image4_label, "picture4_after", payload["positive_threshold"])
            predicted_classes.append(pred4["class"])
        except ValueError:
            return jsonify({
                "Message": f"Could not download picture4_after: {payload['picture4_after']['request_image_url']}"
            }), 400

        def most_frequent(List):
            return max(set(List), key=List.count)

        if predicted_classes.count(predicted_classes[0]) == 2:
            predicted_class = "Not sure"
        else:
            predicted_class = str(most_frequent(predicted_classes))
        response = jsonify({
            "model_version": "2.0.0",
            "positive_threshold": payload["positive_threshold"],
            "study_id": payload["study_id"],
            "via_result": predicted_class,
            "picture1_before": {
                "request_image_url": image1_url,
                "pred_class": pred1["class"],
                "negative_confidence": pred1["negative_confidence"],
                "positive_confidence": pred1["positive_confidence"],
            },
            "picture2_before": {
                "request_image_url": image2_url,
                "pred_class": pred2["class"],
                "negative_confidence": pred2["negative_confidence"],
                "positive_confidence": pred2["positive_confidence"],
            }, "picture3_after": {
                "request_image_url": image3_url,
                "pred_class": pred3["class"],
                "negative_confidence": pred3["negative_confidence"],
                "positive_confidence": pred3["positive_confidence"],
            }, "picture4_after": {
                "request_image_url": image4_url,
                "pred_class": pred4["class"],
                "negative_confidence": pred4["negative_confidence"],
                "positive_confidence": pred4["positive_confidence"],
            }
        })
        return response
    except Exception as msg:
        response = jsonify({
            "message": f"Exception error: {msg}"
        })
        print(msg)
        return response, 400

    except AssertionError as msg:
        response = jsonify({
            "message": f"Error: {msg}"
        })
        return response, 400
