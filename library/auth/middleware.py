from django.http import HttpResponse

import library.models
from library.auth.models import AnonymousUser
from library.auth.views.delegate import OAuth


class AuthenticationMiddleware(object):

    def process_request(self, request):
        request.user = AnonymousUser
        person = None

        for try_auth in (self.try_session_auth, self.try_header_auth):
            result = try_auth(request)
            if isinstance(result, HttpResponse):
                return result
            if person is None and result is not None:
                person = result

        if person is not None:
            request.user = person
            request.user.is_anonymous = False

    def try_session_auth(self, request):
        try:
            openid = request.session['openid']
            person = library.models.Person.get(openid=openid)
        except (KeyError, ValueError):
            return
        return person

    def try_header_auth(self, request):
        method = request.method
        url = request.build_absolute_uri()

        if request.META.get('HTTP_AUTHORIZATION', '').startswith('OAuth '):
            preamble, auth_header = request.META['HTTP_AUTHORIZATION'].split(' ', 1)
            auth_params = re.split(r'\s*,\s*', auth_header)
        else:
            auth_params = request.POST or {}

        try:
            consumer, token = OAuth.unpack(auth_params, method, url)
        except OAuth.BadRequestError, exc:
            resp = HttpResponse(
                content=str(exc),
                content_type='text/plain',
                status=401,
            )
            resp['WWW-Authenticate'] = 'OAuth realm="giraffe"'
            return resp
        request.consumer, request.token, request.oauth_params = consumer, token, auth_params

        if token is None:
            return
        return token.person
