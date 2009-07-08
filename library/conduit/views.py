from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import django.utils.simplejson as json

from library.api.views import api_error, json_encoder
from library.conduit import conduits
from library.views import allowed_methods


def search(request):
    return render_to_response(
        'library/conduit/search.html',
        {
            "conduits": conduits,
        },
        context_instance=RequestContext(request),
    )


@allowed_methods('POST')
@api_error
def do_search(request):
    post = dict((k.encode('utf8'), v) for k, v in request.POST.items())
    for conduit in conduits:
        results = conduit.search(**post)
        return HttpResponse(
            content=json.dumps(results, indent=4, default=json_encoder),
            content_type="application/json",
        )
