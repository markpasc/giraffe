from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'library.views.stream', {'openid': 'http://markpasc.org/mark/'}),
)
