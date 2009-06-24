from cStringIO import StringIO
from functools import wraps
import sys
import traceback

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
import django.utils.simplejson as json
from google.appengine.ext import db

from library.auth import admin_only
import library.models


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


@admin_only
@allowed_methods("GET")
@api_error
def browserpage(request):
    return render_to_response(
        'library/api.html',
        context_instance=RequestContext(request),
    )


@admin_only
@allowed_methods("GET")
@api_error
def types(request):
    types = library.models.model_for_kind.keys()
    return HttpResponse(
        content=json.dumps(types, indent=4),
        content_type='application/json',
    )


@admin_only
@allowed_methods("POST")
@api_error
def code(request):
    codestr = request.raw_post_data
    codestr = codestr.replace('\r\n', '\n')
    try:
        code = compile(codestr, '<post>', 'exec')
    except Exception, exc:
        return HttpResponse(
            content='%s compiling code:\n\n%s\n\nGiven code: %s'
                % (type(exc).__name__, traceback.format_exc(), codestr),
            content_type='text/plain',
            status=400,
        )

    real_stdout = sys.stdout
    real_stderr = sys.stderr
    try:
        spool = StringIO()
        sys.stdout = spool
        sys.stderr = spool
        exec code in {}
    except Exception, exc:
        return HttpResponse(
            content='%s executing code:\n\n%s'
                % (type(exc).__name__, traceback.format_exc()),
            content_type='text/plain',
            status=400,
        )
    else:
        return HttpResponse(
            content=spool.getvalue(),
            content_type='text/plain',
        )
    finally:
        sys.stdout = real_stdout
        sys.stderr = real_stderr


@admin_only
@allowed_methods("POST", "GET")
@api_error
def list(request, kind):
    try:
        cls = library.models.model_with_kind(kind)
    except ValueError:
        return HttpResponseNotFound(
            content='No such resource %r' % kind,
            content_type='text/plain',
        )

    # Show a list if it's a GET.
    if request.method == "GET":
        q = cls.all()
        objs = q[0:10]
        resp = [x.as_data() for x in objs]

        return HttpResponse(
            content=json.dumps(resp, indent=4),
            content_type='application/json',
        )

    # Otherwise try to make one.
    try:
        data = json.loads(request.raw_post_data)
    except Exception, exc:
        return HttpResponse(
            content="%s creating %s:\n\n%s\n\nGiven data: %s"
                % (type(exc).__name__, cls.__name__, traceback.format_exc(),
                   request.raw_post_data),
            content_type='text/plain',
            status=400,
        )

    kwargs = dict([(k.encode('utf-8'), v) for k, v in data.iteritems()])

    try:
        obj = cls(**kwargs)
        obj.put()
    except Exception, exc:
        return HttpResponse(
            content="%s creating %s:\n\n%s\n\nGiven data: %s"
                % (type(exc).__name__, cls.__name__, traceback.format_exc(),
                   json.dumps(data, indent=4)),
            content_type='text/plain',
            status=400,
        )

    item = reverse(
        'library.views.api.item',
        kwargs={'kind': kind, 'key': obj.key()},
    )
    return HttpResponseRedirect(item)


@admin_only
@allowed_methods("GET", "PUT", "POST", "DELETE")
@api_error
def item(request, kind, key):
    try:
        cls = library.models.model_with_kind(kind)
    except ValueError:
        return HttpResponseNotFound(
            content='No such resource type %r' % kind,
            content_type='text/plain',
        )

    try:
        obj = cls.get(key)
    except db.BadKeyError:
        return HttpResponse(
            content='Sequence %r is not a legitimate object key' % key,
            content_type='text/plain',
            status=400,
        )
    except db.KindError:
        return HttpResponse(
            content='Key %r is not for an object of type %r' % (key, kind),
            content_type='text/plain',
            status=400
        )

    if obj is None:
        return HttpResponseNotFound(
            content='No such %r resource %r' % (kind, key),
            content_type='text/plain',
        )

    if request.method == "DELETE":
        try:
            obj.delete()
        except Exception, exc:
            return HttpResponse(
                content="%s deleting %s instance:\n\n%s"
                    % (type(exc).__name__, cls.__name__, traceback.format_exc()),
                content_type='text/plain',
                status=400,
            )
        return HttpResponse(status=207)

    if request.method != "GET":
        try:
            data = json.loads(request.raw_post_data)
        except Exception, exc:
            return HttpResponse(
                content="%s creating %s:\n\n%s\n\nGiven data: %s"
                    % (type(exc).__name__, cls.__name__, traceback.format_exc(),
                       request.raw_post_data),
                content_type='text/plain',
                status=400,
            )

        for k, v in data.iteritems():
            try:
                setattr(obj, k, v)
            except Exception, exc:
                return HttpResponse(
                    content="%s setting %s instance attribute %s:\n\n%s"
                        % (type(exc).__name__, cls.__name__, k,
                           traceback.format_exc()),
                    content_type='text/plain',
                    status=400,
                )

        # If it was a PUT, delete everything that wasn't specified.
        if request.method == "PUT":
            for prop in obj.all_properties():
                if prop not in data:
                    delattr(obj, prop)

        try:
            obj.put()
        except Exception, exc:
            return HttpResponse(
                content="%s saving modified %s instance:\n\n%s"
                    % (type(exc).__name__, cls.__name__, traceback.format_exc()),
                content_type='text/plain',
                status=400,
            )

    return HttpResponse(
        content=json.dumps(obj.as_data(), indent=4),
    )
