"""
The default set of plugins that come with giraffe.
"""

import logging
from os.path import join, dirname

import yaml

from giraffe.accounts import AccountHandler


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
        return [self.template_with_account(x, account) for x in self.feeds]


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
