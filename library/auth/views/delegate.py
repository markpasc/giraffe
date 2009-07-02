import binascii
import hashlib
from time import time
from urllib import urlencode, quote

from django.http import HttpResponseUnauthorized, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from library.auth.decorators import *
from library.models.delegate import *
from library.views import allowed_methods


class OAuth(object):

    timestamp_skew = 500  # seconds

    class BadRequestError(Exception):
        pass

    @classmethod
    def unpack(cls, request, method, url, timestamp_skew=None):
        try:
            consumer_key = request['oauth_consumer_key']
        except KeyError:
            # That's okay, but there's nothing to unpack.
            return None, None
        consumer = Consumer.get(oauthkey=consumer_key)
        if consumer is None:
            raise cls.BadRequestError('Request is from an unknown consumer')

        try:
            version = request['oauth_version']
        except KeyError:
            pass
        else:
            if version != '1.0':
                raise cls.BadRequestError('Request is not for OAuth version 1.0')

        try:
            timestamp = int(request['oauth_timestamp'])
        except KeyError:
            raise cls.BadRequestError('Request has no timestamp')
        except ValueError:
            raise cls.BadRequestError('Request has a non-numeric timestamp')
        if timestamp_skew is None:
            timestamp_skew = cls.timestamp_skew
        now = int(time())
        if timestamp < now - timestamp_skew:
            raise cls.BadRequestError('Request has an expired timestamp %d (needed after %s)'
                % (timestamp, now - timestamp_skew))
        if now + timestamp_skew < timestamp:
            raise cls.BadRequestError('Request has a timestamp %d from the future (needed before %s)'
                % (timestamp, now + timestamp_skew))

        try:
            token_key = request['oauth_token']
        except KeyError:
            # That's okay.
            token = None
        else:
            token = Token.get(id=token_key, consumer=consumer)
            if token is None:
                raise cls.BadRequestError('Request has an unknown token %r' % token_key)

        try:
            squib = request['oauth_nonce']
        except KeyError:
            raise cls.BadRequestError('Request has no nonce')
        if Squib.get(keys_only=True, consumer=consumer_key, value=squib) is not None:
            raise cls.BadRequestError('Request has a used nonce')

        try:
            signature = request['oauth_signature']
            sign_meth = request['oauth_signature_method']
        except KeyError:
            raise cls.BadRequestError('Request is not signed')
        if sign_meth != 'HMAC-SHA1':
            raise cls.BadRequestError('Request is signed with unknown method %r, not HMAC-SHA1'
                % sign_meth)
        signed_params = [(k, v) for k, v in request.iteritems()
            if k.startswith('oauth_') and k != 'oauth_signature']

        key = quote(consumer.secret, '') + '&'
        if token is not None:
            key += quote(token.secret, '')

        signed_params = sorted(signed_params)
        sign_base = urlencode(signed_params)
        sign_base = '&'.join((method, url, sign_base))

        if signature != cls.sign(key, sign_base):
            raise cls.BadRequestError('Request is incorrectly signed (tried signing %r)'
                % sign_base)

        return consumer, token

    @classmethod
    def sign(cls, key, sign_base):
        hashed = hmac.new(key, sign_base, hashlib.sha1)
        encoded = binascii.b2a_base64(hashed.digest())[:-1]
        return encoded


@auth_forbidden
def request(request):
    try:
        consumer = request.consumer
    except AttributeError:
        return HttpResponseUnauthorized(
            content='Authorization required for this resource',
            content_type='text/plain',
            headers={'WWW-Authenticate': 'OAuth realm="giraffe"'},
        )

    callback = request.oauth_params['oauth_callback']
    token = Token(callback=callback, consumer=consumer.id)
    token.save()

    token_data = {
        'oauth_token': token.id,
        'oauth_token_secret': token.secret,
    }

    return HttpResponse(
        content=urlencode(token_data),
        content_type='application/x-www-form-urlencoded',
    )


@auth_required
@allowed_methods("GET")
def ask(request):
    return render_to_response(
        'library/authorize.html',
        {
            'token': request.GET.get('token'),
        },
        context_instance=RequestContext(request),
    )


@auth_required
@allowed_methods("POST")
def authorize(request):
    token = Token.get(id=request.POST['token'])

    token.authed_by = request.user
    token.save()

    return HttpResponseRedirect(token.callback)


@auth_forbidden
def access(request):
    try:
        consumer = request.consumer
        token = request.token
        person = token.authed_by
    except AttributeError:
        return HttpResponseUnauthorized(
            content='Authorization required for this resource',
            content_type='text/plain',
            headers={'WWW-Authenticate': 'OAuth realm="giraffe"'},
        )

    newtoken = Token(consumer=consumer, person=person)
    newtoken.save()

    token.remove()

    token_data = {
        'oauth_token': newtoken.id,
        'oauth_token_secret': newtoken.secret,
    }

    return HttpResponse(
        content=urlencode(token_data),
        content_type='application/x-www-form-urlencoded',
    )
