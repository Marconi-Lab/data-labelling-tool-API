import os
from PIL import Image as Img

from flask import request,  Blueprint, jsonify, url_for
from werkzeug.utils import secure_filename

import application as app
from application.models import Image, Item, User, Assignment, Dataset
from ..admin import allowed_file

external_blueprint = Blueprint("external", __name__)