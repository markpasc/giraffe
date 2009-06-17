from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'library.views.pages.stream', {'openid': 'http://markpasc.org/mark/'}, name="home"),
    url(r'^profile/(?P<slug>.*)', 'library.views.pages.profile', name="profile"),
    url(r'^api$', 'library.views.api.browserpage'),
    url(r'^api/(?P<kind>[^/+]+)$', 'library.views.api.list'),
    url(r'^api/(?P<kind>[^/+]+)/(?P<id>.+)$', 'library.views.api.item'),
)
