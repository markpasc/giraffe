from django.conf.urls.defaults import *

urlpatterns = patterns('library.auth.views',
    url(r'^signin$',  'signin',  name="signin"),
    url(r'^signout$', 'signout', name="signout"),
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
