from functools import wraps
import time

from django.conf import settings
from django.http import HttpResponseRedirect
from google.appengine.api import users
from openid.store import interface, nonce

import library.models as models


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


AnonymousUser = _AnonymousUserClass()


class AuthenticationMiddleware(object):

    def process_request(self, request):
        try:
            openid = request.session['openid']
            person = models.Person.all().filter(openid=openid)[0]
            if person is None:
                raise ValueError()
        except (KeyError, ValueError):
            request.user = AnonymousUser


def auth_forbidden(fn):
    @wraps(fn)
    def check_for_anon(request, *args, **kwargs):
        if request.user is AnonymousUser:
            return fn(request, *args, **kwargs)
        return HttpResponseRedirect(reverse('home'))

    return check_for_anon


def auth_required(fn):
    @wraps(fn)
    def check_for_auth(request, *args, **kwargs):
        if request.user is AnonymousUser:
            this_url = request.get_full_path()
            login_url = users.create_login_url(this_url)
            return HttpResponseRedirect(login_url)
        return fn(request, *args, **kwargs)

    return check_for_auth


def admin_only(fn):
    @wraps(fn)
    def check_for_admin(request, *args, **kwargs):
        if request.user is not AnonymousUser:
            email = request.user.email
            for admin in settings.ADMINS:
                if admin[1] == email:
                    return fn(request, *args, **kwargs)
        # Send 'em to re-login.
        this_url = request.get_full_path()
        login_url = users.create_login_url(this_url)
        return HttpResponseRedirect(login_url)

    return check_for_admin


class OpenIDStore(interface.OpenIDStore):

    def storeAssociation(self, server_url, association):
        a = models.Association(server_url=server_url)
        for key in ('handle', 'secret', 'issued', 'lifetime', 'assoc_type'):
            setattr(a, key, getattr(association, key))
        a.save()

    def getAssociation(self, server_url, handle=None):
        q = models.Association.all().filter(server_url=server_url)
        if handle is not None:
            q.filter(handle=handle)

        # No expired associations.
        q.filter(expires__lte=int(time.time()))

        # Get the futuremost association.
        q.order('-expires')

        try:
            a = q[0]
        except IndexError:
            return
        else:
            return a.as_openid_association()

    def removeAssociation(self, server_url, handle):
        q = models.Association.all().filter(server_url=server_url, handle=handle)
        a = q[0]
        if a is None:
            return False

        a.delete()
        return True

    def useNonce(self, server_url, timestamp, salt):
        now = int(time.time())
        if timestamp < now - nonce.SKEW or now + nonce.SKEW < timestamp:
            return False

        data = dict(server_url=server_url, timestamp=timestamp, salt=salt)

        q = models.Squib.all().filter(**data)
        if q[0]:
            return False

        s = models.Squib(**data)
        s.save()

    def cleanup(self):
        self.cleanupAssociations()
        self.cleanupNonces()

    def cleanupAssociations(self):
        now = int(time.time())
        q = models.Association.all(keys_only=True).filter(expires__lt=now - nonce.SKEW)
        db.delete(q.fetch(100))

    def cleanupNonces(self):
        now = int(time.time())
        q = models.Squib.all(keys_only=True).filter(timestamp__lt=now - nonce.SKEW)
        db.delete(q.fetch(100))
