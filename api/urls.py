from django.conf.urls.defaults import *

urlpatterns = patterns('api.views',
    url(r'^api$', 'types'),
    url(r'^api/code$', 'code'),
    url(r'^api/myself$', 'myself'),
    url(r'^api/(?P<kind>[^/+]+)$', 'list'),
    url(r'^api/(?P<kind>[^/+]+)/offset=(?P<offset>\d+)$', 'list'),
    url(r'^api/(?P<kind>[^/+]+)/(?P<key>.+)$', 'item'),
)
