def permission_required(function):
    def wrap(self, request, *args, **kwargs):
        auth_headers = request.headers.get("Authorization")
        access_token = auth_headers.split(" ")[1]
        if not access_token:
            abort(401)
        if not request.headers.get("is_admin"):
            abort(403)
        return function(self, request, *args, **kwargs)
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
        # def decorator(f):
        #     @wraps(f)
        #     def decorated_function(*args, **kwargs):
        #         if not current_user.can(permission):
        #             abort(403)
        #         return f(*args, **kwargs)
        #     return decorated_function
        # return decorator