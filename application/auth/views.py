from . import auth_blueprint

from flask.views import MethodView
from flask import make_response, request, jsonify, url_for, render_template_string
from application.models import Assignment, User, BlackListToken, Dataset
from application.utils.token import generate_verification_token, confirm_verification_token
from application.utils.email import send_email

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
                is_admin = post_data['is_admin']
                user = User(email=email, password=password, is_admin=is_admin)
                user.firstname = post_data['firstname']
                user.lastname = post_data['lastname']
                user.age = post_data['age']
                user.gender = post_data['gender']
                user.country = post_data['country']
                user.city = post_data['city']
                user.street = post_data['street']
                user.description = post_data['description']
                user.experience = post_data['experience']
                user.is_verified = False
                
                # email verification token
                print("Generating token...")
                token = generate_verification_token(email)
                print(f"Token: {token}")
                print("Creating verification...")
                verification_email = url_for('auth.verify_email', token=token, _external=True)
                html = render_template_string(
                    "<h2>Marconi ML annotator email verification</h2><p>Thanks for signing up! Please follow\
                        this link to activate your account: </p><p><a href='{{ verification_email }}'>\
                        {{ verification_email }}</a></p> <br> <p>Thanks!</p>", verification_email=verification_email
                )
                subject  =  "Marconi ML annotator email verification"
                send_email(email, subject, html)
                if "site" in post_data:
                    user.site = post_data["site"]
                user.save()

                # datasets = list(Dataset.query.filter_by(project_id=int(post_data['project_id'])).all())
                # print(f"datasets {datasets}")
                # for dataset in datasets:
                #     assignment = Assignment(user_id=int(user.id), dataset_id=int(dataset.id))
                #     assignment.save()

                response = {
                    'message': 'You registered successfully.'
                }
                # return a response notifying the user that they registered successfully
                return make_response(jsonify(response)), 201
            except Exception as e:
                # An error occured, therefore return a string message containing the error
                print(e)
                response = {
                    'message': "Internal server error"
                }
                return make_response(jsonify(response)), 500
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
                        'is_verified': user.is_verified,
                        'id': user.id,
                        'firstname': user.firstname,
                        'lastname':user.lastname,
                        'email': user.email,
                        'project_admin': user.project_admin
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
