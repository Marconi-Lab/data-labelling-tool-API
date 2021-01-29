from . import admin_blueprint
from flask.views import MethodView
from flask import Blueprint, make_response, request, jsonify, url_for, current_app
from application.models import User, Dataset, Image, Item, Assignment
from werkzeug.utils import secure_filename
import random
import string
from application.models import User, Item
import os
import application as app

from dotenv import load_dotenv
load_dotenv()

allowed_extensions = set(['image/jpeg', 'image/png', 'jpeg'])
uploads_dir = os.path.join(os.path.dirname(app.__file__), os.environ.get("UPLOAD_FOLDER"))
def allowed_file(filename):
    return filename in allowed_extensions

def get_random_string():
    # Random string with the combination of lower and upper case
    letters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(letters) for i in range(20))
    return result_str

class itemUploadView(MethodView):
    """This class uploads a new item."""
    def post(self):
        """Handle POST request for this view. URL ---> /admin/<int:dataset_id>/items"""
        try:
            item_name = get_random_string()
            dataset_id = str(request.data.get("dataset_id"))
            item = Item(name=item_name, dataset_id=dataset_id)
            item.save()
            # print("Item: ", item.id)
            # print("Request: ", request.data)
            images = request.files.getlist("images")
            # print("Request files: ", request.files)
            # print("images: ",images)
            urls = list()
            for image in images:
                if image and allowed_file(image.content_type):
                    image_name = secure_filename(image.filename)
                    item_id = item.id
                    image.save(os.path.join(uploads_dir, image_name))
                    image_URL = url_for(os.environ.get("UPLOAD_FOLDER"), filename=image_name, _external=True)
                    urls.append(image_URL)
                    image_upload = Image(name=image_name, item_id=item_id, image_URL=image_URL)
                    image_upload.save()
            response = {
                "message": "Item was successfully added",
                "item_id": item.id,
                "images": urls
            }
            return make_response(jsonify(response)), 201
        except Exception as e:
            response = {
                "message": str(e)
            }
            print("Message: ", e)
            return make_response(jsonify(response)), 500

# Define the API resource             
item_upload_view = itemUploadView.as_view('item_upload_view')

admin_blueprint.add_url_rule(
    '/admin/datasets/item/',
    view_func=item_upload_view,
    methods=['POST']
)
