"""
Installs feed URL overrides to make certain feeds get loaded via the CliqSet feedproxy,
which turns generic feeds into activity streams feeds.
"""



def make_username_override(*feed_keys):
    def cb(account):
        username = account.username
        return map(lambda k : "http://api.cliqset.com/feed?svcuser=%s&feedid=%s" % (username, k), feed_keys)
    return cb


def make_userid_override(*feed_keys):
    def cb(account):
        user_id = account.user_id
        return map(lambda k : "http://api.cliqset.com/feed?svcuser=%s&feedid=%s" % (user_id, k), feed_keys)
    return cb


overrides = {}


overrides["youtube.com"] = make_username_override("youtubevideosposted", "youtubevideosfavorited")
overrides["hulu.com"] = make_username_override("huluactivityposted")
overrides["last.fm"] = make_username_override("lastfmsongsplayed", "lastfmsongsfavorited", "lastfmweblogsposted")
overrides["deviantart.com"] = make_username_override("deviantartweblogsposted", "deviantartphotosposted", "deviantartphotosfavorited")
overrides["hulu.com"] = make_username_override("huluactivityposted")


def install_all():
    from giraffe.accounts import register_feed_urls_override
    for domain in overrides:
        register_feed_urls_override(domain, overrides[domain])

