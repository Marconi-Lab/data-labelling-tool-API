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
