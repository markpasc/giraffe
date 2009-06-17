from functools import wraps
import traceback

from django.http import Http404, HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
from google.appengine.ext import db

from library.auth import auth_required
import library.models
from library.models import Person, Asset, Action, Blog


def stream(request, openid):
    try:
        me = Person.all().filter(openid=openid)[0]
    except IndexError:
        raise Http404

    blog = Blog.all().filter(person=me).order('-posted')[0:10]
    actions = [x.action for x in blog]

    return render_to_response(
        'library/stream.html',
        {
            'blogger': me,
            'actions': actions,
        },
        context_instance=RequestContext(request),
    )


def profile(request, slug):
    try:
        person = Person.all().filter(slug=slug)[0]
    except IndexError:
        raise Http404

    actions = Action.all().filter(person=person).order('-when')[0:10]

    return render_to_response(
        'library/profile.html',
        {
            'person': person,
            'actions': actions,
        },
        context_instance=RequestContext(request),
    )


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


@auth_required
@allowed_methods("GET")
@api_error
def api_browserpage(request):
    return render_to_response(
        'library/api.html',
        context_instance=RequestContext(request),
    )


@auth_required
@allowed_methods("POST", "GET")
@api_error
def api_list(request, kind):
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

    try:
        obj = cls(**data)
    except Exception, exc:
        return HttpResponse(
            content="%s creating %s:\n\n%s\n\nGiven data: %s"
                % (type(exc).__name__, cls.__name__, traceback.format_exc(),
                   json.dumps(data, indent=4)),
            content_type='text/plain',
            status=400,
        )

    item = reverse('library.views.api_item',
        {'kind': kind, 'id': obj.key()})
    return HttpResponseRedirect(item)


@auth_required
@allowed_methods("GET", "PUT")
@api_error
def api_item(request, kind, id):
    try:
        cls = library.models.model_with_kind(kind)
    except ValueError:
        return HttpResponseNotFound(
            content='No such resource %r' % '/'.join((kind, id)),
            content_type='text/plain',
        )

    try:
        obj = cls.get(id)
    except (db.BadKeyError, db.KindError):
        return HttpResponseNotFound(
            content='No such resource %r' % '/'.join((kind, id)),
            content_type='text/plain',
        )

    if request.method == "GET":
        return HttpResponse(
            content=json.dumps(obj.as_data(), indent=4),
        )

    raise NotImplementedError()
