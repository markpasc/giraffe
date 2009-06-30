from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from library.models import Person, Asset, Action, Blog


def stream(request, openid):
    try:
        me = Person.all().filter(openid=openid)[0]
    except IndexError:
        raise Http404

    blog = Blog.all().filter(person=me, privacy_group="public")
    blog.order('-posted')
    actions = [x.action for x in blog[0:10]]

    return render_to_response(
        'library/stream.html',
        {
            'blogger': me,
            'actions': actions,
        },
        context_instance=RequestContext(request),
    )


def profile(request, slug):
    person = Person.get(slug=slug)
    if person is None:
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


def asset(request, slug):
    asset = Asset.get(slug=slug)
    if asset is None:
        raise Http404

    actions = asset.actions.filter(person=asset.author, verb=Action.verbs.post)
    thread = asset.thread_members

    return render_to_response(
        'library/asset.html',
        {
            'person': asset.author,
            'actions': actions,
            'thread': thread,
        },
        context_instance=RequestContext(request),
    )
