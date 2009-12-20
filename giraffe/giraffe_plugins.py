"""
The default set of plugins that come with giraffe.
"""

import logging
from os.path import join, dirname

import yaml

from giraffe import accounts
from giraffe.accounts import AccountHandler
from giraffe import activitystreams


logging.debug("Loading the built-in plugins")


class YamlAccountHandler(AccountHandler):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def provider_name(self):
        return self.provider

    def handled_domains(self):
        return self.domains

    @classmethod
    def template_with_account(cls, template, account):
        return template % {
            'username': account.username,
            'user_id':  account.user_id,
        }

    def profile_url_for_account(self, account):
        return self.template_with_account(self.profile_url, account)

    def activity_feed_urls_for_account(self, account):
        if "feeds" in self.__dict__:
            return [self.template_with_account(x, account) for x in self.feeds]
        else:
            return []


yamlz = yaml.load(file(join(dirname(__file__), 'providers.yaml')))
for provider in yamlz:
    logging.debug('YAY %r', provider)
    handler = YamlAccountHandler(**provider)
    AccountHandler.register(handler)


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

def feed_is_youtube_favorites(et, account):
    from giraffe import atom
    id_elem = et.getroot().findtext(atom.ATOM_ID)
    return id_elem.endswith("favorites")

def fix_youtube_video_ids(et, account):
    from giraffe import atom
    feed_elem = et.getroot()
    entry_elems = feed_elem.findall(atom.ATOM_ENTRY)

    for entry_elem in entry_elems:
        id_elem = entry_elem.find(atom.ATOM_ID)
        media_group_elem = entry_elem.find("{http://search.yahoo.com/mrss/}group")
        video_id_elem = media_group_elem.find("{http://gdata.youtube.com/schemas/2007}videoid")
        canonical_id = "tag:youtube.com,2008:video:%s" % video_id_elem.text
        id_elem.text = canonical_id

    return et

accounts.register_feed_mangler("youtube.com", accounts.chain_feed_manglers(
    accounts.conditional_feed_mangler(
        feed_is_youtube_favorites,
        accounts.verb_feed_mangler(activitystreams.type_uri("favorite")),
    ),
    accounts.object_type_feed_mangler(activitystreams.type_uri("video")),
    fix_youtube_video_ids
))
accounts.register_feed_mangler("livejournal.com", accounts.object_type_feed_mangler(activitystreams.type_uri("blog-entry")))

def fix_flickr_links(et, account):
    # TODO: Extract the photo URL out of the content and synthesize
    # link rel="enclosure" and rel="preview" with appropriate width/height
    # so that we can render thumbnails and larger images in the activity
    # streams.
    return et

accounts.register_feed_mangler("flickr.com", accounts.chain_feed_manglers(
    accounts.object_type_feed_mangler(activitystreams.type_uri("photo")),
    fix_flickr_links
))
