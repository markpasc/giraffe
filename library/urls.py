from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'library.views.pages.stream', {'openid': 'http://markpasc.org/mark/'}, name="home"),
    url(r'^profile/(?P<slug>.*)', 'library.views.pages.profile', name="profile"),
)

urlpatterns += patterns('library.views.api',
    url(r'^shell$', 'browserpage'),
    url(r'^api$', 'types'),
    url(r'^api/code$', 'code'),
    url(r'^api/(?P<kind>[^/+]+)$', 'list'),
    url(r'^api/(?P<kind>[^/+]+)/(?P<key>.+)$', 'item'),
)

urlpatterns += patterns('library.views.auth',
    url(r'^login$',  'login',  name="login"),
    url(r'^login/start$', 'start_openid'),
    url(r'^login/complete$', 'complete_openid'),
    url(r'^logout$', 'logout', name="logout"),
)
