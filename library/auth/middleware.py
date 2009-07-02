import library.models
from library.auth.models import AnonymousUser
from library.auth.views.delegate import OAuth


class AuthenticationMiddleware(object):

    def process_request(self, request):
        request.user = AnonymousUser

        session_person = self.try_session_auth(request)
        header_person = self.try_header_auth(request)

        person = session_person or header_person
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
            preamble, auth_header = request['Authorization'].split(' ', 1)
            auth_params = re.split(r'\s*,\s*', auth_header)
            consumer, token = OAuth.unpack(auth_params, method, url)
        else:
            auth_params = request.POST or {}

        consumer, token = OAuth.unpack(auth_params, method, url)
        request.consumer, request.token, request.oauth_params = consumer, token, auth_params

        if token is None:
            return
        return token.person
