from functools import wraps

from django.http import HttpResponseRedirect
from google.appengine.api import users


class _AnonymousUserClass(object):

    class Error(Exception):
        pass

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = object.__new__(cls)
        return cls.instance

    def _cant_do_that(*args, **kwargs):
        raise _AnonymousUserClass.Error("That's an anonymous user, silly")

    for x in ('user_id', 'email', 'nickname'):
        locals()[x] = _cant_do_that


AnonymousUser = _AnonymousUserClass()


class AuthenticationMiddleware(object):

    def process_request(self, request):
        user = users.get_current_user()
        if user:
            request.user = user
        else:
            request.user = AnonymousUser


def auth_required(fn):
    @wraps(fn)
    def check_for_auth(request, *args, **kwargs):
        if request.user is AnonymousUser:
            this_url = request.get_full_path()
            login_url = users.create_login_url(this_url)
            return HttpResponseRedirect(login_url)
        return fn(request, *args, **kwargs)

    return check_for_auth
