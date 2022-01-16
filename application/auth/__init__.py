from flask import Blueprint, jsonify

from application.utils.token import confirm_verification_token

from application.models import User

#Authentication blueprint instance
auth_blueprint = Blueprint('auth', __name__)

from . import views

@auth_blueprint.route('/confirm/<token>', methods=['GET'])
def verify_email(token):
    try:
        email = confirm_verification_token(token)

        user = User.query.filter_by(email=email).fist()
        if user.isVerified:
            response = jsonify({
                "message": "Invalid input"
            })
            response.status_code = 422
            return response
        else:
            user.isVerified = True
            user.save()
            response = jsonify({
                'message': 'E-mail verified, you can proceed to login now.'
            })
            response.status_code = 200
            return response
    except Exception as e:
        print(e)
        return e