from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
import django.util.simplejson as json
from google.appengine.api import users
from google.appengine.api.urlfetch import fetch
import oauth
from openid.consumer import consumer, discover
from openid.extensions import sreg

from library.auth import auth_required, auth_forbidden, log
from library.auth import make_person_from_response
from library.auth import AnonymousUser, OpenIDStore


@auth_forbidden
def signin(request, nexturl=None):
    return render_to_response(
        'library/signin.html',
        {},
        context_instance=RequestContext(request),
    )


@auth_forbidden
def start_openid(request):
    openid_url = request.POST.get('openid_url', None)
    if not openid_url:
        username = request.POST.get('openid_username', None)
        pattern = request.POST.get('openid_pattern', None)
        if username and pattern:
            openid_url = pattern.replace('{name}', username)
    if not openid_url:
        request.flash.put(loginerror="An OpenID as whom to sign in is required.")
        return HttpResponseRedirect(reverse('login'))
    log.debug('Attempting to sign viewer in as %r', openid_url)

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


class OAuthDance(object):
    class Homg(Exception):
        pass

    def request_token(self, csr):
        req = oauth.OAuthRequest.from_consumer_and_token(csr,
            http_method="GET", http_url=self.request_token_url)
        req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), csr)

        resp = fetch(req.to_url(), method=req.get_normalized_http_method())
        if resp.status_code != 200:
            raise self.Homg('Oops fetching request token?! %d %r' % (resp.status_code, resp.content))
        token = oauth.OAuthToken.from_string(resp.content)

        return token

    def authorize_token_url(self, token, callback):
        req = oauth.OAuthRequest.from_token_and_callback(
            token,
            callback=callback,
            http_url=self.authorization_url,
        )
        return req.to_url()

    def access_token(self, csr, token):
        req = oauth.OAuthRequest.from_consumer_and_token(
            csr,
            token=token,
            http_url=self.access_token_url,
        )
        req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), csr)

        resp = fetch(req.to_url(), method=req.get_normalized_http_method())
        if resp.status_code != 200:
            raise self.Homg('Oops fetching access token?! %d %r' % (resp.status_code, resp.content))
        token = oauth.OAuthToken.from_string(resp.content)

        return token


class TwitterDance(OAuthDance):
    request_token_url = 'http://twitter.com/oauth/request_token'
    access_token_url = 'http://twitter.com/oauth/access_token'
    authorize_url = 'http://twitter.com/oauth/authorize'


@auth_forbidden
def start_twitter(request):
    csr = oauth.OAuthConsumer(*settings.TWITTER_KEY)
    dance = TwitterDance()
    token = dance.request_token(csr)
    request.session['twitter_request_token'] = str(token)
    auth_url = dance.authorize_token_url(token, reverse('library.views.auth.complete_twitter'))
    return HttpResponseRedirect(redirect_url)


@auth_forbidden
def complete_twitter(request):
    request_token_str = request.session['twitter_request_token']
    del request.session['twitter_request_token']
    request_token = oauth.OAuthToken.from_string(request_token_str)

    csr = oauth.OAuthConsumer(*settings.TWITTER_KEY)
    dance = TwitterDance()
    token = dance.access_token(csr, request_token)
    request.session['twitter_access_token'] = str(token)

    return HttpResponseRedirect(reverse('library.views.auth.confirm_twitter'))


@auth_forbidden
def confirm_twitter(request):
    access_token_str = request.session['twitter_access_token']
    del request.session['twitter_access_token']
    access_token = oauth.OAuthToken.from_string(access_token_str)
    csr = oauth.OAuthConsumer(*settings.TWITTER_KEY)

    confirm_url = 'http://twitter.com/account/verify_credentials.json'
    req = oauth.OAuthRequest.from_consumer_and_token(csr, access_token,
        http_method="GET", http_url=confirm_url)
    req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), csr, access_token)

    headers = req.to_header()
    resp = fetch(confirm_url, method="GET", headers=headers)
    if resp.status_code != 200:
        raise self.Homg('Could not confirm twitter sign-in: %d %s' % (self.status_code, self.content))

    # Yay.
    data = json.loads(resp.content)
    openid = "http://twitter.com/%s" % (data['screen_name'],)
    person = Person.get(openid=openid)
    if person is None:
        person = Person(openid=openid)

    person.name = data.get('name')
    person.userpic = data.get('profile_image_url')
    person.save()

    request.session['openid'] = openid
    return HttpResponseRedirect(reverse('home'))


@auth_required
def signout(request):
    del request.session['openid']
    del request.user
    return HttpResponseRedirect(reverse('home'))
