from django.conf.urls.defaults import *

urlpatterns = patterns('library.views.pages',
    url(r'^$', 'stream', {'openid': 'http://markpasc.org/mark/'}, name="home"),
    url(r'^profile/(?P<slug>[^/]*)$', 'profile', name="profile"),
    url(r'^asset/(?P<slug>[^/]*)$', 'asset', name="asset"),
    url(r'^asset/(?P<slug>[^/]*)/comments$', 'comment', name="comment"),
    url(r'^\d{4}/\d{2}/(?P<slug>[^/]*)\.html$', 'asset_redirect'),
    url(r'^post$',      'post',),
)

urlpatterns += patterns('',
    url(r'^shell$', 'api.views.shell', {'template': 'library/shell.html'}),
)

urlpatterns += patterns('library.views.images',
    url(r'^image$', 'post'),
    url(r'^image/(?P<key>[^/.]*)\.(?P<ext>[^/]*)$', 'get'),
)

urlpatterns += patterns('library.views.pages',
    url(r'^feed$', 'stream',
        {'openid': 'http://markpasc.org/mark/',
         'template': 'library/stream_feed.xml',
         'content_type': 'application/atom+xml'},
        name="home_feed"),
    url(r'^profile/(?P<slug>[^/]*)/feed$', 'profile',
        {'template': 'library/profile_feed.xml',
         'content_type': 'application/atom+xml'},
        name="profile_feed"),
)
