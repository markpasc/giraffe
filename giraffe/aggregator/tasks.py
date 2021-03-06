import logging
from urllib import urlencode
from urlparse import urljoin
from xml.etree import ElementTree

from celery.decorators import task
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
import httplib2


@task
def subscribe(feed_url, sub_pk):
    log = logging.getLogger('%s.subscribe' % __name__)

    h = httplib2.Http()
    resp, cont = h.request(feed_url)
    if resp.status != 200:
        # No feed means we can't subscribe to notifications.
        log.warning('HTTP response %d %s trying to fetch feed %s', resp.status, resp.reason, feed_url)
        return

    # Look for the hub link.
    try:
        doc = ElementTree.fromstring(cont)
        elems = doc.findall('{http://www.w3.org/2005/Atom}link')
        log.debug("elems is %r", elems);
        hubs = [elem for elem in elems if elem.attrib['rel'] == 'hub']
        hub_url = hubs[0].attrib['href']
    except Exception, exc:
        log.warning('%s trying to find hub in feed %s: %s', type(exc).__name__, feed_url, str(exc))
        hub_url = "http://pubsubhubbub.appspot.com/"

    # Try to subscribe.
    callback_root = 'http://%s/' % Site.objects.get_current().domain
    callback = urljoin(callback_root, reverse('aggregator-callback', kwargs={"sub_pk":sub_pk}))
    log.debug("My hub.callback will be %s", callback)
    subreq = {
        'hub.callback': callback,
        'hub.mode': 'subscribe',
        'hub.topic': feed_url,
        'hub.verify': 'async',
    }
    resp, cont = h.request(uri=hub_url, method='POST', body=urlencode(subreq),
        headers={'Content-Type': 'application/x-www-form-urlencoded'})

    if resp.status not in (202, 204):
        log.warning('HTTP response %d %s trying to request subscription to feed %s from hub %s',
            resp.status, resp.reason, feed_url, hub_url)

    # Even if the response was correct, we want to mark the subscription as
    # push when the hub verifies the subscription, so we're done.
    return
