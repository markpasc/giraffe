import re

from django.conf.urls.defaults import *


api_url_re = re.compile(r"""
    ^api
    (?:
        /
        (?P<kind>[^/]+)
        (?:
            /
            (?P<id>.+)
        )
    )?
""", re.VERBOSE)

urlpatterns = patterns('',
    url(r'^$', 'library.views.stream', {'openid': 'http://markpasc.org/mark/'}, name="home"),
    url(r'^profile/(?P<slug>.*)', 'library.views.profile', name="profile"),
    url(r'^api$', 'library.views.api_browserpage'),
    url(r'^api/(?P<kind>[^/+]+)$', 'library.views.api_list'),
    url(r'^api/(?P<kind>[^/+]+)/(?P<id>.+)$', 'library.views.api_item'),
)
