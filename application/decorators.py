from functools import wraps
from flask import request, abort
from application.models import User, BlackListToken

def permission_required():
    def _permission_required(f):
        @wraps(f)
        def __permission_required(*args, **kwargs):
            auth_headers = request.headers.get("Authorization")
            if not auth_headers:
                abort(401)
            access_token = auth_headers.split(" ")[1]
            if access_token:
                try:
                    is_blacklisted = BlackListToken.check_blacklist(access_token)
                    if is_blacklisted:
                        abort(401, "Token blacklisted")
                    user_id = User.decode_token(access_token)
                    if not str(user_id) == str(request.headers.get("user_id")):
                        abort(401, "Not authorized" + user_id + "!= "+request.headers.get("user_id"))
                except Exception as e:
                    abort(401, e)
            if not request.headers.get("is_admin"):
                abort(403)
            return f(*args, **kwargs)
        return __permission_required
    return _permission_required

def user_is_authenticated():
    def _user_is_authenticated(f):
        @wraps(f)
        def __user_is_authenticated(*args, **kwargs):
            auth_headers = request.headers.get("Authorization")
            if not auth_headers:
                abort(401)
            access_token = auth_headers.split(" ")[1]
            if access_token:
                try:
                    is_blacklisted = BlackListToken.check_blacklist(access_token)
                    if is_blacklisted:
                        abort(401, "Token blacklisted")
                    user_id = User.decode_token(access_token)
                    if not str(user_id) == str(request.headers.get("user_id")):
                        abort(401, "Not authorized" + user_id + "!= "+request.headers.get("user_id"))
                except Exception as e:
                    abort(401, e)
            return f(*args, **kwargs)
        return __user_is_authenticated
    return _user_is_authenticated
