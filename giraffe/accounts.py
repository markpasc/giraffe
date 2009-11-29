
handler_for_domain = {}

DEFAULT_HANDLER = None

class AccountHandler:
    """
    Abstract base class for classes that handle accounts.
    """

    @classmethod
    def for_domain(cls, domain):
        if domain in handler_for_domain:
            return handler_for_domain[domain]
        else:
            return DEFAULT_HANDLER

    @classmethod
    def register(cls, handler):
        # FIXME: Should detect if we get a domain collision
        # between two handlers.
        domains = handler.handled_domains()
        for domain in domains:
            handler_for_domain[domain] = handler

    def handled_domains(self):
        return []

    def provider_name(self):
        return None

    def profile_url_for_account(self, account):
        return None

    def display_username_for_account(self, account):
        return account.username

    def activity_feed_urls_for_account(self, account):
        return []

    def custom_polled_urls_for_account(self, account):
        return []

DEFAULT_HANDLER = AccountHandler()

# TODO: Make a generic accounthandler that can easily be seeded from
# a configuration file like MT Action Streams does.
# For now it's just code.

class WebsiteAccountHandler(AccountHandler):

    # For a "website" account, the domain is the empty string,
    # the username contains the URL of the website home page
    # and the user_id contains the URL of the main feed for that
    # site.

    def profile_url_for_account(self, account):
        return account.username

    def activity_feed_urls_for_account(self, account):
        if account.user_id != "":
            return [ account.user_id ]
        else:
            return []

    def handled_domains(self):
        return [ "" ]

AccountHandler.register(WebsiteAccountHandler());

