def permission_required(function):
    def wrap(self, request, *args, **kwargs):
        if not request.headers.is_admin:
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