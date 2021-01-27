from flask import Blueprint

#Authentication blueprint instance
auth_blueprint = Blueprint('auth', __name__)

from . import views