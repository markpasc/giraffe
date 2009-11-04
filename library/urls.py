from django.conf.urls.defaults import *

urlpatterns = patterns('library.views.pages',
    url(r'^$', 'stream',
        {'openid': 'http://markpasc.org/mark/',
         'empty_ok': True},
        name="home"),
    url(r'^page/(?P<page>\d+)$', 'stream',
        {'openid': 'http://markpasc.org/mark/',
         'empty_ok': True},
        name="home_paged"),
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
    url(r'^upload_image$', 'browser_post'),
    url(r'^image$', 'raw_post'),
    url(r'^image/(?P<key>[^/.]*)\.(?P<ext>[^/]*)$', 'get'),
)

urlpatterns += patterns('',
    url(r'^feed$', 'django.views.generic.simple.redirect_to',
        {'url': 'http://feeds2.feedburner.com/bestendtimesever'}),
)

urlpatterns += patterns('library.views.pages',
    url(r'^feeeed$', 'stream',
        {'openid': 'http://markpasc.org/mark/',
         'template': 'library/stream_feed.xml',
         'content_type': 'application/atom+xml'},
        name="home_feed"),
    url(r'^profile/(?P<slug>[^/]*)/feed$', 'profile',
        {'template': 'library/profile_feed.xml',
         'content_type': 'application/atom+xml'},
        name="profile_feed"),
)
