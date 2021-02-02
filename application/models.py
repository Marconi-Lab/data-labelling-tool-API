from application import db
# from flask_user import UserMixin
from flask_bcrypt import Bcrypt
import jwt
from flask import current_app
from datetime import datetime, timedelta

class Dataset(db.Model):
    """This class represents the datasets table"""
    
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    classes = db.Column(db.ARRAY(db.String))
    classes2 = db.Column(db.ARRAY(db.String))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __init__(self, name, classes):
        """initialize with name."""
        self.name = name
        self.classes = classes

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Dataset.query.all()

    @staticmethod
    def count_all():
        return Dataset.query.count()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "<Dataset: {}>".format(self.name)

class User(db.Model):
    """This class defines the user table"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.String)

    def __init__(self, email, password, username, is_admin):
        """Initialize the user with an email, username and a password"""
        self.email = email
        self.password = Bcrypt().generate_password_hash(password).decode()
        self.username = username
        self.is_admin = is_admin
        
    def password_is_valid(self, password):
        """Checks password against it's hash"""
        return Bcrypt().check_password_hash(self.password, password)

    def save(self):
        """Save a user to the database"""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return User.query.all()
    
    @staticmethod
    def count_all():
        return User.query.count()

    def generate_token(self, user_id):
        """Generates access Token"""

        try:
            # set up a payload with an expiration time
            payload = {
                'exp': datetime.utcnow() + timedelta(minutes=60),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            # create the byte string token using the payload and the SECRET key
            jwt_string = jwt.encode(
                payload,
                current_app.config.get("SECRET"),
                'HS256'
            )
            return jwt_string
        except Exception as e:
            # return and error in string format if an exception occurs
            return str(e)
    
    @staticmethod
    def decode_token(token):
        """Decodes the access token from the Authorization header."""
        try:
            # try to decode the token using our SECRET variable
            payload = jwt.decode(token, current_app.config.get('SECRET'), algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            # the token is expired, return an error string
            return "Expired token. Please login to get a new token"
        except jwt.InvalidTokenError:
            # the token is invalid, return an error string
            return "Invalid token. Please register or login"

class Item(db.Model):
    """This class defines the data items table"""
    
    __tablename__ = "data_items"

    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey(Dataset.id, ondelete="CASCADE"))
    name = db.Column(db.String(255))
    label = db.Column(db.String(255))
    comment = db.Column(db.String(255))
    labelled = db.Column(db.Boolean)
    labelled_by = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="CASCADE"))

    def __init__(self, dataset_id, name):
        """Initialize with dataset_id, label, comment, labelled_status"""
        self.dataset_id = dataset_id
        self.name = name
    def save(self):
        """Save an item
        Applies for both creating an new item and updating an existing item.
        """
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all(dataset_id):
        """This method gets all the items in a dataset"""
        return Item.query.filter_by(dataset_id=dataset_id)

    def delete(self):
        """Deletes the given data item"""
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        """Return a representation of a data item instance"""
        return f"<Data Item: {self.name}"

class Image(db.Model):
    """This class an image belonging to a data item"""

    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey(Item.id, ondelete="CASCADE"))
    image_URL = db.Column(db.String)
    label = db.Column(db.String)
    labelled = db.Column(db.Boolean)
    labelled_by = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="CASCADE"))
    dataset_id = db.Column(db.Integer, db.ForeignKey(Dataset.id, ondelete="CASCADE"))

    def __init__(self, image_URL, name):
        """Initialize image with data item ID and image URL"""
        self.name = name
        self.image_URL = image_URL

    def save(self):
        """Save an image"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Deletes an assigment record"""
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all(item_id):
        """Return all images in a data item"""
        return Image.query.filter_by(item_id=item_id)

    def __repr__(self):
        """Return representation of an image"""
        return f"Image {self.name}"

class Assignment(db.Model):
    """Class for dataset labelling assignments"""
    __tablename__ = "assigniments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id, ondelete="CASCADE"))
    dataset_id = db.Column(db.Integer, db.ForeignKey(Dataset.id, ondelete="CASCADE"))

    def __init__(self, user_id, dataset_id):
        """Initialises an assignment with user_id and dataset_id"""
        self.user_id = user_id
        self.dataset_id = dataset_id

    def save(self):
        """Saves an assignment"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Deletes an assigment record"""
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_user_datasets(user_id):
        """This method gets all the dataset that have been assigned to the given user"""
        return Assignment.query.filter_by(user_id=user_id)


class BlackListToken(db.Model):
    """Model stores blacklisted tokens"""

    __tablename__ = "blacklist_tokens"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.now()

    def __repr__(self):
        return f"id: token: {self.token}"

    def save(self):
        """Saves an assignment"""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def check_blacklist(auth_token):
        res = BlackListToken.query.filter_by(token=str(auth_token)).first()
        if res:
            return True
        else:
            return False