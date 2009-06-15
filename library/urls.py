from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'library.views.stream', {'openid': 'http://markpasc.org/mark/'}, name="home"),
)
