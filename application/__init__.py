from dotenv import load_dotenv
from flask_api import FlaskAPI
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from instance.config import app_config

load_dotenv()

db = SQLAlchemy()


def create_app(config_name):
    from application.models import Dataset, User, Item, Image
    from application.decorators import permission_required

    app = FlaskAPI(__name__, instance_relative_config=True)
    CORS(app)
    app.config['CORS_HEADERS'] = ['Content-Type', 'Authorization', 'is_admin']
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # user_manager = UserManager(app, db, User)
    db.init_app(app)

    from .auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .admin import admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .user import user_blueprint
    app.register_blueprint(user_blueprint)
    return app
