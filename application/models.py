from application import db
from flask_user import UserMixin
from flask_bcrypt import Bcrypt

class Datasets(db.Model):
    """This class represents the datasets table"""
    
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    classes = db.Column(db.ARRAY(db.String))
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
        return Datasets.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "<Dataset: {}>".format(self.name)

class User(db.Model, UserMixin):
    """This class defines the user table"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')

    def __init__(self, email, password, username):
        """Initialize the user with an email, username and a password"""
        self.email = email
        self.password = Bcrypt().generate_password_hash(password).decode()
        self.username = username

    def password_is_valid(self, password):
        """Checks password against it's hash"""
        return Bcrypt().check_password_hash(self.password, password)

    def save(self):
        """Save a user to the database"""
        db.session.add(self)
        db.session.commit()

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
                algorithm='HS256'
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
            payload = jwt.decode(token, current_app.config.get('SECRET'))
            return payload['sub']
        except jwt.ExpiredSignatureError:
            # the token is expired, return an error string
            return "Expired token. Please login to get a new token"
        except jwt.InvalidTokenError:
            # the token is invalid, return an error string
            return "Invalid token. Please register or login"
# Define the Role data-model
class Role(db.Model):

    __tablename__ = 'roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))