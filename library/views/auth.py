from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from google.appengine.api import users
from openid.consumer import consumer, discover
from openid.extensions import sreg

from library.auth import auth_required, auth_forbidden
from library.auth import make_person_from_response
from library.auth import AnonymousUser, OpenIDStore


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

    ar.addExtension(sreg.SRegRequest(optional=('nickname', 'fullname', 'email')))

    def whole_reverse(view):
        return request.build_absolute_uri(reverse(view))

    return_to = whole_reverse('library.views.auth.complete_openid')
    redirect_url = ar.redirectURL(whole_reverse('home'), return_to)
    return HttpResponseRedirect(redirect_url)


@auth_forbidden
def complete_openid(request):
    csr = consumer.Consumer(request.session, OpenIDStore())
    resp = csr.complete(request.GET, request.build_absolute_uri())
    if isinstance(resp, consumer.CancelResponse):
        return HttpResponseRedirect(reverse('home'))
    elif isinstance(resp, consumer.FailureResponse):
        request.flash.put(loginerror=resp.message)
        return HttpResponseRedirect(reverse('login'))
    elif isinstance(resp, consumer.SuccessResponse):
        make_person_from_response(resp)
        request.session['openid'] = resp.identity_url
        return HttpResponseRedirect(reverse('home'))


@auth_required
def logout(request):
    del request.session['openid']
    del request.user
    return HttpResponseRedirect(reverse('home'))
