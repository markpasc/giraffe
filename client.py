#!/usr/bin/env python

import sys

import oauth
import optfunc
import httplib2


class TwitterConsumer(oauth.OAuthConsumer):
    request_token_url = 'http://twitter.com/oauth/request_token'
    access_token_url = 'http://twitter.com/oauth/access_token'
    authorize_url = 'http://twitter.com/oauth/authorize'


consumers = {
    'twitter': TwitterConsumer,
}


class OAuthClient(httplib2.Http):
    class OAuthError(Exception):
        pass

    def _raise_unsuccessful_response(self, msg, resp, content):
        if resp.status < 400:
            return

        if resp.get('content-type', '') == "text/plain":
            raise self.OAuthError('%s: %d %s: %s'
                % (msg, resp.status, resp.reason, content))

        raise self.OAuthError('%s: %d %s' % (msg, resp.status, resp.reason))

    def request_token(self, csr):
        req = oauth.OAuthRequest.from_consumer_and_token(csr,
            http_method="GET", http_url=csr.request_token_url)
        req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), csr, None)

        resp, content = self.request(uri=req.to_url(), method=req.get_normalized_http_method())
        self._raise_unsuccessful_response('Unsuccessful response getting a request token',
            resp, content)

        token = oauth.OAuthToken.from_string(content)
        return token

    def authorize_token_url(self, csr, token, callback):
        req = oauth.OAuthRequest.from_token_and_callback(
            token,
            callback=callback,
            http_url=csr.authorize_url,
        )
        return req.to_url()

    def access_token(self, csr, token):
        req = oauth.OAuthRequest.from_consumer_and_token(
            csr,
            token=token,
            http_url=csr.access_token_url,
        )
        req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), csr, token)

        resp, content = self.request(uri=req.to_url(), method=req.get_normalized_http_method())
        self._raise_unsuccessful_response('Unsuccessful response exchanging for an access token',
            resp, content)

        token = oauth.OAuthToken.from_string(content)
        return token

    def signed_request(self, uri, method="GET", headers=None, csr=None, token=None, **kwargs):
        req = oauth.OAuthRequest.from_consumer_and_token(csr, token,
            http_method=method, http_url=uri)
        req.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), csr, token)

        if headers is None:
            headers = req.to_header()
        else:
            headers.update(req.to_header())

        return self.request(uri=uri, method=method, headers=headers, **kwargs)


def main(url=None, consumer=None, token=None):
    csr_kind, csr_key, csr_secret = consumer.split(':')
    consumer_class = consumers[csr_kind]
    csr = consumer_class(key=csr_key, secret=csr_secret)

    h = OAuthClient()

    if token is None:
        token = h.request_token(csr)
        print "Your new request token:  %s:%s" % (token.key, token.secret)

        req_url = h.authorize_token_url(csr, token, url)
        print "Authorization URL:  %s" % (req_url,)

        return

    token_key, token_secret = token.split(':')
    token = oauth.OAuthToken(token_key, token_secret)

    if url is None:
        token = h.access_token(csr, token)
        print "Your new access token:  %s:%s" % (token.key, token.secret)
        return

    resp, content = h.signed_request(uri=url, csr=csr, token=token)

    for k, v in resp.items():
        print '%s: %s' % (k, v)
    print
    print content


if __name__ == '__main__':
    optfunc.run(main)
