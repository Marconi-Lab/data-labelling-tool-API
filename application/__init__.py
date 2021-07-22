from dotenv import load_dotenv
from flask_api import FlaskAPI
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from instance.config import app_config
import flask_monitoringdashboard as dashboard
import os
load_dotenv()

db = SQLAlchemy()


def create_app(config_name):
    from application.models import Dataset, User, Item, Image
    from application.decorators import permission_required

    app = FlaskAPI(__name__, instance_relative_config=True)
    CORS(app)
    dashboard.config.init_from(file="../dashboard_config.cfg")
    dashboard.bind(app)
    app.config['CORS_HEADERS'] = ['Content-Type', 'Authorization', 'is_admin']
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['EXTERNAL_UPLOADS'] = os.path.join(os.path.dirname(__file__), os.environ.get("UPLOAD_FOLDER"), "external" )
    # user_manager = UserManager(app, db, User)
    with app.app_context():
        db.init_app(app)
        from .auth import auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix="/api/v1")

        from .admin import admin_blueprint
        app.register_blueprint(admin_blueprint, url_prefix="/api/v1")

        from .user import user_blueprint
        app.register_blueprint(user_blueprint, url_prefix="/api/v1")

        from .external import external_blueprint
        app.register_blueprint(external_blueprint, url_prefix="/api/v1")
    return app
