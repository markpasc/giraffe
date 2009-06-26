import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from openid.consumer import consumer, discover
from openid.extensions import sreg

from library.auth.decorators import auth_forbidden
from library.auth.models import OpenIDStore, make_person_from_response


log = logging.getLogger(__name__)


@auth_forbidden
def start(request):
    openid_url = request.POST.get('openid_url', None)
    if not openid_url:
        username = request.POST.get('openid_username', None)
        pattern = request.POST.get('openid_pattern', None)
        if username and pattern:
            openid_url = pattern.replace('{name}', username)
    if not openid_url:
        request.flash.put(loginerror="An OpenID as whom to sign in is required.")
        return HttpResponseRedirect(reverse('signin'))
    log.debug('Attempting to sign viewer in as %r', openid_url)

    csr = consumer.Consumer(request.session, OpenIDStore())
    try:
        ar = csr.begin(openid_url)
    except discover.DiscoveryFailure, exc:
        request.flash.put(error=exc.message)
        return HttpResponseRedirect(reverse('signin'))

    ar.addExtension(sreg.SRegRequest(optional=('nickname', 'fullname', 'email')))

    def whole_reverse(view):
        return request.build_absolute_uri(reverse(view))

    return_to = whole_reverse('library.auth.views.regular.complete')
    redirect_url = ar.redirectURL(whole_reverse('home'), return_to)
    return HttpResponseRedirect(redirect_url)


@auth_forbidden
def complete(request):
    csr = consumer.Consumer(request.session, OpenIDStore())
    resp = csr.complete(request.GET, request.build_absolute_uri())
    if isinstance(resp, consumer.CancelResponse):
        return HttpResponseRedirect(reverse('home'))
    elif isinstance(resp, consumer.FailureResponse):
        request.flash.put(error=resp.message)
        return HttpResponseRedirect(reverse('signin'))
    elif isinstance(resp, consumer.SuccessResponse):
        make_person_from_response(resp)
        request.session['openid'] = resp.identity_url
        return HttpResponseRedirect(reverse('home'))
