from django.conf.urls.defaults import *

urlpatterns = patterns('library.conduit.views',
    url(r'^conduit/search$', 'search'),
    url(r'^conduit/searchies$', 'do_search'),
)
