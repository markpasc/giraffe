#!/usr/bin/env python

import mimetypes
import sys

import oauth
import optfunc
import httplib2


class TwitterConsumer(oauth.OAuthConsumer):
    request_token_url = 'http://twitter.com/oauth/request_token'
    authorize_url = 'http://twitter.com/oauth/authorize'
    access_token_url = 'http://twitter.com/oauth/access_token'


class LocalConsumer(oauth.OAuthConsumer):
    request_token_url = 'http://localhost:8000/delegate/request'
    authorize_url = 'http://localhost:8000/delegate/ask'
    access_token_url = 'http://localhost:8000/delegate/access'


class BeeConsumer(oauth.OAuthConsumer):
    request_token_url = 'http://www.bestendtimesever.com/delegate/request'
    authorize_url = 'http://www.bestendtimesever.com/delegate/ask'
    access_token_url = 'http://www.bestendtimesever.com/delegate/access'


consumers = {
    'twitter': TwitterConsumer,
    'local': LocalConsumer,
    'bee': BeeConsumer,
}


class OAuthClient(httplib2.Http):

    def __init__(self, *args, **kwargs):
        self.verbose = kwargs.pop('verbose', False)
        super(OAuthClient, self).__init__(*args, **kwargs)

    class OAuthError(Exception):
        pass

    def _raise_unsuccessful_response(self, msg, resp, content):
        if resp.status < 400:
            return

        if resp.get('content-type', '') == "text/plain":
            raise self.OAuthError('%s: %d %s: %s'
                % (msg, resp.status, resp.reason, content))
        elif self.verbose:
            raise self.OAuthError('%s: %d %s\n\n%s\n\n%s'
                % (msg, resp.status, resp.reason,
                   '\n'.join(['%s: %s' % (k, v) for k, v in resp.items()]),
                   content))

        raise self.OAuthError('%s: %d %s' % (msg, resp.status, resp.reason))

    def request_token(self, csr, callback='oob'):
        req = oauth.OAuthRequest.from_consumer_and_token(csr,
            http_method="POST", http_url=csr.request_token_url)
        req.set_parameter('oauth_callback', callback)

        signer = oauth.OAuthSignatureMethod_HMAC_SHA1()
        if self.verbose:
            req.set_parameter('oauth_signature_method', signer.get_name())
            base = signer.build_signature_base_string(req, csr, None)
            print "Signed base string: %s\n" % (base,)

        req.sign_request(signer, csr, None)

        request = dict(uri=req.to_url(), method=req.get_normalized_http_method(),
            body=req.to_postdata())
        if self.verbose:
            print "%s %s" % (request['method'], request['uri'])
            print
            print request['body']
        resp, content = self.request(**request)
        self._raise_unsuccessful_response('Unsuccessful response getting a request token',
            resp, content)

        try:
            token = oauth.OAuthToken.from_string(content)
        except KeyError:
            raise ValueError("Oops, couldn't decode token from response: %s\n%s"
                % ('\n'.join('%s: %s' % (k, v) for k, v in resp.iteritems()), content))
            token = None

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
            http_method="POST",
        )

        signer = oauth.OAuthSignatureMethod_HMAC_SHA1()
        if self.verbose:
            req.set_parameter('oauth_signature_method', signer.get_name())
            base = signer.build_signature_base_string(req, csr, None)
            print "Signed base string: %s\n" % (base,)

        req.sign_request(signer, csr, token)

        request = dict(uri=req.to_url(), method=req.get_normalized_http_method(), body=req.to_postdata())
        if self.verbose:
            print "%s %s" % (request['method'], request['uri'])
            print
            print request['body']

        resp, content = self.request(**request)
        self._raise_unsuccessful_response('Unsuccessful response exchanging for an access token',
            resp, content)

        token = oauth.OAuthToken.from_string(content)
        return token

    def signed_request(self, uri, method=None, headers=None, csr=None, token=None, **kwargs):
        if method is None:
            method = "GET"
        verbose = kwargs.pop('verbose', False)

        req = oauth.OAuthRequest.from_consumer_and_token(csr, token,
            http_method=method, http_url=uri)
        signer = oauth.OAuthSignatureMethod_HMAC_SHA1()
        req.set_parameter('oauth_signature_method', signer.get_name())
        if verbose:
            print "Signature base string: %r" % (signer.build_signature_base_string(req, csr, token),)
        req.sign_request(signer, csr, token)

        if headers is None:
            headers = req.to_header()
        else:
            headers.update(req.to_header())

        if verbose:
            print "%s %s" % (method, uri)
            for k, v in headers.items():
                print "%s: %s" % (k, v)
            print

        return self.request(uri=uri, method=method, headers=headers, **kwargs)


def main(url=None, consumer=None, token=None, method=None, filename=None, verbose=False):
    if consumer is None:
        print "The consumer info is required"
        return

    csr_kind, csr_key, csr_secret = consumer.split(':')
    consumer_class = consumers[csr_kind]
    csr = consumer_class(key=csr_key, secret=csr_secret)

    h = OAuthClient(verbose=verbose)

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

    body, headers = None, {}
    if filename is not None:
        try:
            body = file(filename, 'rb').read()
        except IOError, exc:
            print "Could not read file %s: %s" % (filename, exc)
        else:
            content_type = mimetypes.guess_type(filename)[0]
            if content_type is not None:
                headers['content-type'] = content_type
            headers['content-length'] = str(len(body))

    resp, content = h.signed_request(uri=url, method=method, body=body,
        headers=headers, csr=csr, token=token, verbose=verbose)

    for k, v in resp.items():
        print '%s: %s' % (k, v)
    print
    print content


if __name__ == '__main__':
    optfunc.run(main)
