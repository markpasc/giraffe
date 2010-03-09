from django.conf.urls.defaults import *


urlpatterns = patterns('giraffe.views',
    url(r'^$', 'activity_stream', {'stream_key': 'markpasc'}),
)
