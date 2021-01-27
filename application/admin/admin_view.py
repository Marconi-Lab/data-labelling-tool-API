from flask.views import MethodView
from flask import Blueprint, make_response, request, jsonify
from application.models import User, Dataset, Image, Item, Assignment