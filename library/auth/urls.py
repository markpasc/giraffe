from django.conf.urls.defaults import *

urlpatterns = patterns('library.auth.views',
    url(r'^signin$',  'signin',  name="signin"),
    url(r'^signout$', 'signout', name="signout"),
    url(r'^editprofile$', 'editprofile', name="editprofile"),
)

urlpatterns += patterns('library.auth.views.regular',
    url(r'^signin/start$', 'start'),
    url(r'^signin/complete$', 'complete'),
)

urlpatterns += patterns('library.auth.views.twitter',
    url(r'^signin/twitter/start$', 'start'),
    url(r'^signin/twitter/complete$', 'complete'),
    url(r'^signin/twitter/confirm$', 'confirm'),
)

urlpatterns += patterns('library.auth.views.delegate',
    url(r'^delegate/request$', 'request'),
    url(r'^delegate/ask$', 'ask'),
    url(r'^delegate/authorize$', 'authorize'),
    url(r'^delegate/access$', 'access'),
)
