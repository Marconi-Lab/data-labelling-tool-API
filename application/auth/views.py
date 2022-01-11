from . import auth_blueprint

from flask.views import MethodView
from flask import make_response, request, jsonify
from application.models import User, BlackListToken


class RegistrationView(MethodView):
    """This class registers a new user."""

    def post(self):
        """Handle POST request for this view. Url ---> /auth/register/"""

        # Query to see if the user already exists
        user = User.query.filter_by(email=request.data['email']).first()

        if not user:
            # There is no user so we'll try to register them
            try:
                post_data = request.data
                # Register the user
                email = post_data['email']
                password = post_data['password']
                username = post_data['username']
                is_admin = post_data['is_admin']
                user = User(email=email, password=password, username=username, is_admin=is_admin)
                user.firstname = post_data['firstname']
                user.lastname = post_data['lastname']
                user.age = post_data['age']
                user.gender = post_data['gender']
                user.country = post_data['country']
                user.city = post_data['city']
                user.street = post_data['street']
                user.description = post_data['description']
                user.experience = post_data['experience']
                
                if "site" in post_data:
                    user.site = post_data["site"]
                user.save()

                response = {
                    'message': 'You registered successfully.'
                }
                # return a response notifying the user that they registered successfully
                return make_response(jsonify(response)), 201
            except Exception as e:
                # An error occured, therefore return a string message containing the error
                response = {
                    'message': str(e)
                }
                return make_response(jsonify(response)), 401
        else:
            # There is an existing user. We don't want to register users twice
            # Return a message to the user telling them that they they already exist
            response = {
                'message': 'User already exists. Please login.'
            }

            return make_response(jsonify(response)), 202


class LoginView(MethodView):
    """This class-based view handles user login and access token generation."""

    def post(self):
        """Handle POST request for this view. Url ---> /auth/login"""
        try:
            # Get the user object using their email (unique to every user)
            user = User.query.filter_by(email=request.data['email']).first()

            # Try to authenticate the found user using their password
            if user and user.password_is_valid(request.data['password']):
                # Generate the access token. This will be used as the authorization header
                access_token = user.generate_token(user.id)
                if access_token:
                    response = {
                        'message': 'You logged in successfully.',
                        'access_token': access_token,
                        'is_admin': user.is_admin,
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                    return make_response(jsonify(response)), 200
            else:
                # User does not exist. Therefore, we return an error message
                response = {
                    'message': 'Invalid email or password, Please try again'
                }
                return make_response(jsonify(response)), 401

        except Exception as e:
            # Create a response containing an string error message
            response = {
                'message': str(e)
            }
            # Return a server error using the HTTP Error Code 500 (Internal Server Error)
            return make_response(jsonify(response)), 500

class LogoutAPI(MethodView):
    """Logout endpoint"""
    def post(self):
        #get auth token
        auth_header = request.headers.get("Authorization")
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ""
        if auth_token:
            resp = User.decode_token(auth_token)
            if not isinstance(resp, str):
                blacklist_token = BlackListToken(token=auth_token)
                try:
                    blacklist_token.save()
                    response = jsonify({
                        "status": "success",
                        "message": "Successfully logged out."
                    })
                    response.status_code = 200
                    return response
                except Exception as e:
                    responseObject = jsonify({
                        "status": "fail",
                        "message": e
                    })
                    responseObject.status_code = 500
                    return responseObject



# Define the API resource
registration_view = RegistrationView.as_view('registration_view')
login_view = LoginView.as_view('login_view')
logout_view = LogoutAPI.as_view("logout_view")

# Define the rule for the registration url --->  /auth/register/
# Then add the rule to the blueprint
auth_blueprint.add_url_rule(
    '/auth/register/',
    view_func=registration_view,
    methods=['POST'])

# Define the rule for the registration url --->  /auth/login/
# Then add the rule to the blueprint
auth_blueprint.add_url_rule(
    '/auth/login/',
    view_func=login_view,
    methods=['POST']
)

auth_blueprint.add_url_rule(
    "/auth/logout/",
    view_func=logout_view,
    methods=['POST']

)
