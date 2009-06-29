from functools import wraps

from django.http import HttpResponse


def allowed_methods(*methods):
    def wrapper(fn):
        @wraps(fn)
        def check_methods(request, *args, **kwargs):
            if request.method not in methods:
                resp = HttpResponse(
                    content='Method %r not allowed on this resource' % request.method,
                    content_type='text/plain',
                    status=405,
                )
                resp['Allow'] = ', '.join(methods)
                return resp
            return fn(request, *args, **kwargs)
        return check_methods
    return wrapper
