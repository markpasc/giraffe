import library.models
from library.auth.models import AnonymousUser
from library.auth.views.delegate import OAuth


class AuthenticationMiddleware(object):

    def process_request(self, request):
        request.user = AnonymousUser

        person = self.try_session_auth()
        if person is None:
            person = self.try_header_auth()
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

        if request.get('Authorization', '').startswith('OAuth '):
            preamble, auth_header = request['Authorization'].split(' ', 1)
            auth_params = re.split(r'\s*,\s*', auth_header)
            consumer, token = OAuth.unpack(auth_params, method, url)
        else:
            auth_params = request.POST or {}

        request.consumer, request.token = OAuth.unpack(auth_params, method, url)
        request.oauth_params = auth_params

        return token.person
