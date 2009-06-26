from functools import wraps

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from library.auth.models import AnonymousUser


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
            return HttpResponseRedirect(reverse('signin'))
        return fn(request, *args, **kwargs)

    return check_for_auth


def admin_only(fn):
    @wraps(fn)
    def check_for_admin(request, *args, **kwargs):
        if getattr(request.user, 'is_admin', False):
            return fn(request, *args, **kwargs)
        return HttpResponseRedirect(reverse('home'))

    return check_for_admin
