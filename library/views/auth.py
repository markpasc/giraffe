from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from google.appengine.api import users
from openid.consumer import consumer, discover

from library.auth import auth_required, auth_forbidden, AnonymousUser, OpenIDStore


@auth_forbidden
def login(request, nexturl=None):
    return render_to_response(
        'library/auth/login.html',
        {},
        context_instance=RequestContext(request),
    )


@auth_forbidden
def start_openid(request):
    openid_url = request.POST.get('openid_url', None)
    if not openid_url:
        request.flash.put(loginerror="An OpenID as whom to sign in is required.")
        return HttpResponseRedirect(reverse('login'))

    csr = consumer.Consumer(request.session, OpenIDStore())
    try:
        ar = csr.begin(openid_url)
    except discover.DiscoveryFailure, exc:
        request.flash.put(loginerror=exc.message)
        return HttpResponseRedirect(reverse('login'))

    def whole_reverse(view):
        return request.build_absolute_uri(reverse(view))

    return_to = whole_reverse('library.views.auth.complete_openid')
    redirect_url = ar.redirectURL(whole_reverse('home'), return_to)
    return HttpResponseRedirect(redirect_url)


@auth_forbidden
def complete_openid(request):
    csr = consumer.Consumer(request.session, OpenIDStore())
    resp = csr.complete(request.GET, request.build_absolute_uri())
    if isinstance(resp, consumer.SuccessResponse):
        # YAY
        request.session['openid'] = resp.identity_url
        return HttpResponseRedirect(reverse('home'))
    elif isinstance(resp, consumer.CancelResponse):
        return HttpResponseRedirect(reverse('home'))
    elif isinstance(resp, consumer.FailureResponse):
        request.flash.put(loginerror=resp.message)
        return HttpResponseRedirect(reverse('login'))


def logout(request):
    logout_url = reverse('home')
    if request.user is not AnonymousUser:
        logout_url = users.create_logout_url(logout_url)
    return HttpResponseRedirect(logout_url)
