from django.conf import settings
from django.conf.urls.defaults import *

def app_include(app):
    urls = '.'.join((app, 'urls'))
    return (r'^', include(urls))

def has_urls(app):
    urls = '.'.join((app, 'urls'))
    try:
        __import__(urls)
    except ImportError:
        return False
    else:
        return True

urlpatterns = patterns('',
    *[app_include(app) for app in settings.INSTALLED_APPS if has_urls(app)]
)
