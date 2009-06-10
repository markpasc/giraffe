# Force Django to reload its settings before importing any of it.
import os
from django.conf import settings
settings._target = None
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


import logging

from django.core.handlers import wsgi
from django.core import signals
import django.db
from google.appengine.ext.webapp import util


def log_exception(*args, **kwargs):
    logging.exception('Exception in request:')

signals.got_request_exception.connect(log_exception)
signals.got_request_exception.disconnect(django.db._rollback_on_exception)


def main():
    application = wsgi.WSGIHandler()
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
