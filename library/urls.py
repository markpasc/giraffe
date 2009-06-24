from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'library.views.pages.stream', {'openid': 'http://markpasc.org/mark/'}, name="home"),
    url(r'^profile/(?P<slug>.*)', 'library.views.pages.profile', name="profile"),

    url(r'^shell$', 'library.views.api.browserpage'),
    url(r'^api$', 'library.views.api.types'),
    url(r'^api/(?P<kind>[^/+]+)$', 'library.views.api.list'),
    url(r'^api/(?P<kind>[^/+]+)/(?P<key>.+)$', 'library.views.api.item'),

    url(r'^login$',  'library.views.auth.login',  name="login"),
    url(r'^logout$', 'library.views.auth.logout', name="logout"),
)
