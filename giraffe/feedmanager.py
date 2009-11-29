
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

    for account in accounts:
        feed_urls = account.activity_feed_urls()
        callback = activitystreams_feed_callback(account)
        for feed_url in feed_urls:
            urlpoller.register_url(feed_url, callback)


def refresh_feeds():
    urlpoller.poll()


def activitystreams_feed_callback(account):
    def callback(url, result):
        print "Got an activity feed update for "+str(account)+" at "+url
        # "result" is a sufficiently file-like object that
        # we can just pass it right into AtomActivityStream as-is.
        activity_stream = atom.AtomActivityStream(result)

        # FIXME: If activity_stream has a subject, create a link between
        # the account and the subject.

        for atom_activity in activity_stream.activities:
            activity = atom_activity.make_real_activity()
            if activity is not None:
                activity.source_account = account
                activity.source_person = account.person
                activity.save()
    return callback
    
