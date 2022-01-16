from flask import Blueprint, jsonify, redirect

from application.utils.token import confirm_verification_token

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
            response = jsonify({
                "message": "Invalid input"
            })
            response.status_code = 422
            return response
        else:
            user.is_verified = True
            user.save()
            
            return redirect(os.getenv("FRONT_END_LOGIN"), code=302)
    except Exception as e:
        print(e)
        return e