from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from library.models import Person, Asset, Action


def stream(request, openid):
    try:
        me = Person.all().filter('openid =', openid)[0]
    except IndexError:
        raise Http404

    actions = Action.all().filter('who =', me).order('-when')[0:10]

    return render_to_response(
        'library/stream.html',
        {
            'blogger': me,
            'actions': actions,
        },
        context_instance=RequestContext(request),
    )
