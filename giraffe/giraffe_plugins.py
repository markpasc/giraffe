"""
The default set of plugins that come with giraffe.
"""

from giraffe import accounts
AccountHandler = accounts.AccountHandler


class TwitterAccountHandler(AccountHandler):

    def provider_name(self):
        return "Twitter"

    def handled_domains(self):
        return [ "twitter.com" ]

    def profile_url_for_account(self, account):
        return "http://twitter.com/%s" % account.username

    def custom_polled_urls_for_account(self, account):
        from giraffe import twitter;
        return [
            ( "http://twitter.com/statuses/user_timeline/%s.atom" % account.username, twitter.urlpoller_callback ),
        ]

AccountHandler.register(TwitterAccountHandler());


class TypePadProfilesAccountHandler(AccountHandler):

    def provider_name(self):
        return "TypePad"

    def handled_domains(self):
        return [ "profile.typepad.com" ]

    def profile_url_for_account(self, account):
        return "http://profile.typepad.com/%s" % account.username

    def activity_feed_urls_for_account(self, account):
        return [ "http://profile.typepad.com/%s/activity/atom.xml" % account.username ]

AccountHandler.register(TypePadProfilesAccountHandler());


class LiveJournalAccountHandler(AccountHandler):

    def provider_name(self):
        return "LiveJournal"

    def handled_domains(self):
        return [ "livejournal.com" ]

    def profile_url_for_account(self, account):
        return "http://%s.livejournal.com/info" % account.username

    def activity_feed_urls_for_account(self, account):
        return [ "http://%s.livejournal.com/data/atom" % account.username ]

AccountHandler.register(LiveJournalAccountHandler());


class FacebookAccountHandler(AccountHandler):

    def provider_name(self):
        return "Facebook"

    def handled_domains(self):
        return [ "facebook.com" ]

    def profile_url_for_account(self, account):
        return "http://www.facebook.com/profile.php?id=%s" % account.user_id

AccountHandler.register(FacebookAccountHandler());


class CliqsetAccountHandler(AccountHandler):

    def provider_name(self):
        return "Cliqset"

    def handled_domains(self):
        return [ "cliqset.com" ]

    def profile_url_for_account(self, account):
        return "http://cliqset.com/user/%s" % account.username

    def activity_feed_urls_for_account(self, account):
        return [ "http://cliqset.com/feed/atom?uid=%s" % account.username ]

AccountHandler.register(CliqsetAccountHandler());


