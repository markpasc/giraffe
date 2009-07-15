from cStringIO import StringIO
from datetime import datetime
import sys
import traceback

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
import django.utils.simplejson as json
from google.appengine.ext import db
import remoteobjects

from api.decorators import api_error, allowed_methods
from library.auth.decorators import admin_only
import library.models


def json_encoder(obj):
    if isinstance(obj, library.models.Model):
        return obj.as_data()
    if isinstance(obj, remoteobjects.RemoteObject):
        return obj.to_dict()
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("%s instance %r is not json serializable"
        % (type(obj).__name__, obj))


@admin_only
@allowed_methods("GET")
@api_error
def shell(request, template=None):
    if template is None:
        template = 'api/shell.html'

    return render_to_response(
        template,
        context_instance=RequestContext(request),
    )


@admin_only
@allowed_methods("GET")
@api_error
def types(request):
    types = library.models.model_for_kind.keys()
    return HttpResponse(
        content=json.dumps(types, indent=4, default=json_encoder),
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
@allowed_methods("GET")
def myself(request):
    kwargs = {'kind': 'person', 'key': request.user.key()}
    item_url = reverse('api.views.item', kwargs=kwargs)
    url = request.build_absolute_uri(item_url)
    return HttpResponseRedirect(url)


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
            content=json.dumps(resp, indent=4, default=json_encoder),
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

    kwargs = dict()
    for k, v in cls.properties().items():
        if k not in data:
            continue

        value = data[k]

        if isinstance(v, db.ReferenceProperty):
            value = db.Key(value)
        elif isinstance(v, db.DateTimeProperty):
            if '.' in value:
                value = value.split('.', 1)[0]
            value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

        kwargs[k] = value

    try:
        obj = cls(**kwargs)
        obj.put()
    except Exception, exc:
        return HttpResponse(
            content="%s creating %s:\n\n%s\n\nGiven data: %s"
                % (type(exc).__name__, cls.__name__, traceback.format_exc(),
                   json.dumps(data, indent=4, default=json_encoder)),
            content_type='text/plain',
            status=400,
        )

    item = reverse(
        'api.views.item',
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
        content=json.dumps(obj.as_data(), indent=4, default=json_encoder),
    )
