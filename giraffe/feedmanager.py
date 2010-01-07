
"""
A component that glues all of the components together so that we actually poll
feeds that are associated with the registered accounts and hand them off
to the feed parsing code.
"""

from giraffe import models
from giraffe import urlpoller
from giraffe import atom

# TODO: Always call this on startup so that the urlpoller
# is always primed to poll?
# For now, we just explitly call this before we tell the urlpoller to
# poll in the admin command that actually runs a poll cycle.

def init():
    accounts = models.Account.objects.all()

    from giraffe import accounts as accounts_module

    for account in accounts:
        feed_urls_override = accounts_module.get_feed_urls_override_for_domain(account.domain)
        if feed_urls_override:
            feed_urls = feed_urls_override(account)
        else:
            feed_urls = account.activity_feed_urls()
            
        callback = atom.urlpoller_callback(account)
        
        for feed_url in feed_urls:
            urlpoller.register_url(feed_url, callback)

        other_urls = account.custom_polled_urls()
        for url_tuple in other_urls:
            url = url_tuple[0]
            callback = url_tuple[1](account)
            urlpoller.register_url(url, callback)


def refresh_feeds():
    urlpoller.poll()


