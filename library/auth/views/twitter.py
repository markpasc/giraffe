from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
import django.utils.simplejson as json
from google.appengine.api.urlfetch import fetch
import oauth

from library.auth.decorators import auth_forbidden
from library.models import Person


class OAuthDance(object):
    class Homg(Exception):
        pass

    def request_token(self, csr):
        req = oauth.OAuthRequest.from_consumer_and_token(csr,
            http_method="GET", http_url=self.request_token_url)
        req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), csr, None)

        resp = fetch(req.to_url(), method=req.get_normalized_http_method(),
            deadline=10)
        if resp.status_code != 200:
            raise self.Homg('Oops fetching request token?! %d %r' % (resp.status_code, resp.content))
        token = oauth.OAuthToken.from_string(resp.content)

        return token

    def authorize_token_url(self, token, callback):
        req = oauth.OAuthRequest.from_token_and_callback(
            token,
            callback=callback,
            http_url=self.authorize_url,
        )
        return req.to_url()

    def access_token(self, csr, token):
        req = oauth.OAuthRequest.from_consumer_and_token(
            csr,
            token=token,
            http_url=self.access_token_url,
        )
        req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), csr, token)

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
def start(request):
    csr = oauth.OAuthConsumer(*settings.TWITTER_KEY)
    dance = TwitterDance()
    token = dance.request_token(csr)
    request.session['twitter_request_token'] = str(token)
    auth_url = dance.authorize_token_url(token, reverse('library.auth.views.twitter.complete'))
    return HttpResponseRedirect(auth_url)


@auth_forbidden
def complete(request):
    request_token_str = request.session['twitter_request_token']
    del request.session['twitter_request_token']
    request_token = oauth.OAuthToken.from_string(request_token_str)

    csr = oauth.OAuthConsumer(*settings.TWITTER_KEY)
    dance = TwitterDance()
    token = dance.access_token(csr, request_token)
    request.session['twitter_access_token'] = str(token)

    return HttpResponseRedirect(reverse('library.auth.views.twitter.confirm'))


@auth_forbidden
def confirm(request):
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
