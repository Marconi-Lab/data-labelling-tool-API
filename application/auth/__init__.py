from flask import Blueprint, jsonify, redirect, render_template_string
import os

from application.utils.token import confirm_verification_token
from application.utils.email import send_email
from application.models import User

import os

#Authentication blueprint instance
auth_blueprint = Blueprint('auth', __name__)

from . import views

@auth_blueprint.route('/confirm/<token>', methods=['GET'])
def verify_email(token):
    try:
        email = confirm_verification_token(token)

        user = User.query.filter_by(email=email).first()
        if user.is_verified:
            return redirect(os.getenv("FRONT_END_LOGIN"), code=302)

        else:
            user.is_verified = True
            user.save()
            # send email to admin
            html = render_template_string("<h2>New Project Signup</h2> <p>A new user, {{ email}} has registered for the project.</p>\
                <p>Please login to the <a href='https://marconimlannotator.com/administrator'>system</a>\
                     to add them to the project annotator's list.</p>", email=email)
            subject  =  "New SignUp PRESCRIP PROJECT macronimlannotator"
            reciever1 = os.getenv("PROJECT_ADMIN")
            reciever2 = os.getenv("PROJECT_ADMIN2")
            send_email(reciever1, subject, html)
            send_email(reciever2, subject, html)
            return redirect(os.getenv("FRONT_END_LOGIN"), code=302)

    except Exception as e:
        print(e)
        return e