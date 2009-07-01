from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'library.views.pages.stream', {'openid': 'http://markpasc.org/mark/'}, name="home"),
    url(r'^profile/(?P<slug>[^/]*)', 'library.views.pages.profile', name="profile"),
    url(r'^asset/(?P<slug>[^/]*)$', 'library.views.pages.asset', name="asset"),
    url(r'^asset/(?P<slug>[^/]*)/comments$', 'library.views.pages.comment', name="comment"),
)

urlpatterns += patterns('library.views.api',
    url(r'^shell$', 'browserpage'),
    url(r'^api$', 'types'),
    url(r'^api/code$', 'code'),
    url(r'^api/(?P<kind>[^/+]+)$', 'list'),
    url(r'^api/(?P<kind>[^/+]+)/(?P<key>.+)$', 'item'),
)

urlpatterns += patterns('',
    url(r'^', include('library.auth.urls')),
)
