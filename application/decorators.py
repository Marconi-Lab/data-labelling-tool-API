from functools import wraps
from flask import request, abort

def permission_required():
    def _permission_required(f):
        @wraps(f)
        def __permission_required(*args, **kwargs):
            auth_headers = request.headers.get("Authorization")
            if not auth_headers:
                abort(401)
            access_token = auth_headers.split(" ")[1]
          
            if not request.headers.get("is_admin"):
                abort(403)
            return f(*args, **kwargs)
        return __permission_required
    return _permission_required
        # def decorator(f):
        #     @wraps(f)
        #     def decorated_function(*args, **kwargs):
        #         if not current_user.can(permission):
        #             abort(403)
        #         return f(*args, **kwargs)
        #     return decorated_function
        # return decorator