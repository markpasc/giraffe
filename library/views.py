from functools import wraps
import traceback

from django.http import Http404, HttpResponse, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson as json

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


@auth_required
def api_browserpage(request):
    if request.method not in "GET":
        resp = HttpResponse(
            content='Method %r not allowed on this resource' % request.method,
            content_type='text/plain',
            status=405,
        )
        resp['Allow'] = 'GET'
        return resp

    return render_to_response(
        'library/api.html',
        context_instance=RequestContext(request),
    )


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
@api_error
def api_list(request, kind):
    if request.method not in ("POST", "GET"):
        resp = HttpResponse(
            content='Method %r not allowed on this resource' % request.method,
            content_type='text/plain',
            status=405,
        )
        resp['Allow'] = 'GET, POST'
        return resp

    # What kind are we talking about?
    models_content = [getattr(library.models, x) for x in dir(library.models)]
    try:
        cls = [x for x in models_content
                   if isinstance(x, type)
                   and issubclass(x, library.models.Model)
                   and x is not library.models.Model
                   and x.kind().lower() == kind.lower()][0]
    except IndexError:
        return HttpResponseNotFound(
            content='No such resource %r\nTry: %s' % (kind, ' '.join(classes)),
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
@api_error
def api_item(request, kind, id):
    pass
