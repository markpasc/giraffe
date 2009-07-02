from library.auth.models.regular import *
from library.auth.models.delegate import *


class _AnonymousUserClass(object):

    class Error(Exception):
        pass

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = object.__new__(cls)
        return cls.instance

    def _cant_do_that(*args, **kwargs):
        raise _AnonymousUserClass.Error("That's an anonymous user, silly")

    for x in ('user_id', 'email', 'nickname', 'openid'):
        locals()[x] = _cant_do_that

    is_anonymous = True


AnonymousUser = _AnonymousUserClass()
