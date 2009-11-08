
"""
Package for polling URLs at regular intervals and delivering
their content to other components for processing.
"""

from giraffe.models import PolledURL
import time
import datetime
from django.db import IntegrityError
import urllib2

# TODO: Make these configurable
DEFAULT_POLL_INTERVAL = 3600 # 1 hour
PUSH_ENABLED_POLL_INTERVAL = 86400 # 1 day

BEGINNING_OF_TIME = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(0))

callbacks = {}

def register_urls(urls, callback):
    for url in urls:
        cls.register_url(url, callback)

def register_url(url, callback):

    # If it isn't already in our tracking table then
    # we need to add it.

    url_obj = PolledURL(url = url, notifications_enabled = False, last_fetch_time = BEGINNING_OF_TIME)
    try:
        url_obj.save()
    except IntegrityError:
        # It was already in there.
        pass

    callbacks[url] = callback

def poll():
    # What do we need to poll?
    urls_to_poll = urls_needing_poll()

    now = time.time()
    push_enabled_poll_before = now - PUSH_ENABLED_POLL_INTERVAL
    push_enabled_poll_before_obj = datetime.datetime.utcfromtimestamp(push_enabled_poll_before)

    for url in urls_to_poll:
        if url.notifications_enabled:
            # Impose a longer inter-fetch time on feeds with push enabled
            if url.last_fetch_time > push_enabled_poll_before_obj:
                continue

        if not url.url in callbacks:
            # Don't bother polling if we have no callback to deliver the result to
            continue

        _poll(url)

def force_poll(url):
    """
    Poll a particular URL immediately, regardless of whether it's
    scheduled to be polled now.

    The URL passed in must be one that has previously been registered.
    """
    callback = callbacks[url]
    url = PolledURL.objects.filter(url = url)[0]
    _poll(url)

def _poll(url):
    now = time.time()

    # TODO: Run batches of HTTP requests in parallel to reduce
    # the time we spend hanging around waiting for responses to come back
    req = urllib2.Request(url.url)
    if url.last_fetch_etag:
        req.add_header("If-None-Match", url.last_fetch_etag)

    # FIXME: Should also send If-Modified-Since

    url.last_fetch_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(now))

    result = None

    try:
        result = urllib2.urlopen(req)
    except urllib2.HTTPError as err:
        url.last_fetch_status = err.code
        url.save()
        return

    res = result.info()
    etag = res.getheader("ETag", None)
    if etag is None: etag = ''
    url.last_fetch_etag = etag
    url.last_fetch_status = 200

    callback = callbacks[url.url]
    callback(url.url, result)

    url.save()
    return

def urls_needing_poll():
    now = time.time()
    poll_before = now - DEFAULT_POLL_INTERVAL

    poll_before_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(poll_before))

    return PolledURL.objects.filter(last_fetch_time__lte = poll_before_str)

