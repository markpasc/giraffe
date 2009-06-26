import library.models
from library.auth.models import AnonymousUser


class AuthenticationMiddleware(object):

    def process_request(self, request):
        try:
            openid = request.session['openid']
            person = library.models.Person.get(openid=openid)
            if person is None:
                raise ValueError()
        except (KeyError, ValueError):
            request.user = AnonymousUser
        else:
            request.user = person
            request.user.is_anonymous = False
