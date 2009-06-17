from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from google.appengine.api import users

from library.auth import auth_required, AnonymousUser


@auth_required
def login(request):
    return HttpResponseRedirect(reverse('home'))


def logout(request):
    logout_url = reverse('home')
    if request.user is not AnonymousUser:
        logout_url = users.create_logout_url(logout_url)
    return HttpResponseRedirect(logout_url)
