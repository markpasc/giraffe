from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from library.auth.decorators import auth_required, auth_forbidden
from library.views import allowed_methods


@auth_forbidden
def signin(request, nexturl=None):
    return render_to_response(
        'library/signin.html',
        {},
        context_instance=RequestContext(request),
    )


@auth_required
def signout(request):
    del request.session['openid']
    del request.user
    return HttpResponseRedirect(reverse('home'))


@auth_required
@allowed_methods("POST")
def editprofile(request):
    for field in ('name', 'userpic'):
        setattr(request.user, field, request.POST.get(field))
    request.user.save()
    return HttpResponseRedirect(reverse('home'))
