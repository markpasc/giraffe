from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'library.views.pages.stream', {'openid': 'http://markpasc.org/mark/'}, name="home"),
    url(r'^profile/(?P<slug>[^/]*)', 'library.views.pages.profile', name="profile"),
    url(r'^asset/(?P<slug>[^/]*)$', 'library.views.pages.asset', name="asset"),
    url(r'^asset/(?P<slug>[^/]*)/comments$', 'library.views.pages.comment', name="comment"),
)
