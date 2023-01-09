from flask import (
    Blueprint,
    request,
    jsonify,
    redirect,
    render_template_string,
    url_for,
    render_template,
)
import os
from flask_bcrypt import Bcrypt
from application.utils.token import (
    confirm_verification_token,
    generate_verification_token,
)
from application.utils.email import send_email
from application.models import User

import os

# Authentication blueprint instance
auth_blueprint = Blueprint("auth", __name__)

from . import views


@auth_blueprint.route("/confirm/<token>", methods=["GET"])
def verify_email(token):
    print(f"Verifiying token {token}")
    try:
        email = confirm_verification_token(token)
        print(f"Verifying: {email}")
        user = User.query.filter_by(email=email).first()
        if user and user.is_verified:
            return redirect(os.getenv("FRONT_END_LOGIN"), code=302)

        elif user and not user.is_verified:
            user.is_verified = True
            user.save()
            # send email to admin
            html = render_template_string(
                "<h2>New Project Signup</h2> <p>A new user, {{ email}} has registered for the project.</p>\
                <p>Please login to the <a href='https://cacx.marconilab.org/administrator'>system</a>\
                     to add them to the project annotator's list.</p>",
                email=email,
            )
            subject = "New SignUp PRESCRIP PROJECT macronimlannotator"
            reciever1 = os.getenv("PROJECT_ADMIN")
            reciever2 = os.getenv("PROJECT_ADMIN2")
            send_email(reciever1, subject, html)
            send_email(reciever2, subject, html)
            return redirect(os.getenv("FRONT_END_LOGIN"), code=302)
        else:
            return redirect("https://marconimlannotator.com/signup", code=302)

    except Exception as e:
        print(e)
        response = jsonify({"msg": str(e)})
        response.status_code = 500
        return response


@auth_blueprint.route("/password-reset/", methods=["POST"])
def reset_password():
    try:
        data = request.data
        email = data["email"]
        # Get the user object using their email (unique to every user)
        if User.query.filter_by(email=email).first():
            # send password reset email
            print("Generating token...")
            token = generate_verification_token(email)
            print(f"Token: {token}")
            print("Creating verification...")
            verification_email = url_for(
                "auth.new_password", token=token, _external=True
            )
            html = render_template_string(
                "<h2>Marconi CaCx platform password reset</h2><p>Your password\
                     reset request has been received! Please follow\
                    this link to reset your password: {{ email }}\
                ",
                email=verification_email,
            )
            subject = "Marconi Labelling Platform Password Reset"
            send_email(email, subject, html)

            response = jsonify({"message": "Password reset request received"})
            response.status_code = 201

            return response
        else:
            raise ValueError("Email is not associated with any account!")

    except ValueError as e:
        print(e)
        response = jsonify({"message": "Email is not associated with any account"})
        response.status_code = 400
        return response
    except Exception as e:
        print(e)


@auth_blueprint.route(
    "/new-password/<token>", methods=["POST", "GET"], endpoint="new_password"
)
def new_password(token):
    try:
        if request.method == "POST":
            print(f"data: {request.data.getlist('password')}")
            password = request.data.getlist("password")[0]
            email = confirm_verification_token(token)
            password = Bcrypt().generate_password_hash(password).decode()
            user = User.query.filter_by(email=email).first()
            user.password = password
            user.save()

            return render_template_string(
                "<h2>Password Reset Confirmed</h2> <p>Password for, {{ email }} has been reset successfully.</p>\
                <p>Click <a href='https://cacx.marconilab.org/administrator'>here</a> to login.",
                email=email,
            )

        if request.method == "GET":
            return render_template("password-reset.html", token=token)
    except Exception as e:
        print(e)
