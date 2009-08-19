from functools import wraps
import traceback

from django.http import HttpResponse, HttpResponseServerError


def api_error(fn):
    @wraps(fn)
    def try_that(request, *args, **kwargs):
        try:
            return fn(request, *args, **kwargs)
        except Exception, exc:
            return HttpResponseServerError(
                content=traceback.format_exc(),
                content_type='text/plain',
            )
    return try_that


def allowed_methods(*methods):
    methods = [method.upper() for method in methods]
    def wrapper(fn):
        @wraps(fn)
        def check_methods(request, *args, **kwargs):
            if request.method.upper() not in methods:
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
