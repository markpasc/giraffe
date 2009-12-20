
handler_for_domain = {}
mangler_for_domain = {}
feed_urls_override_for_domain = {}

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

def register_feed_mangler(domain, callback):
    # FIXME: Should detect if we get a domain collision between two manglers
    mangler_for_domain[domain] = callback

def get_feed_mangler_for_domain(domain):
    if domain in mangler_for_domain:
        return mangler_for_domain[domain]
    else:
        def dummy(et, account):
            return et
        return dummy

def register_feed_urls_override(domain, callback):
    # FIXME: Should detect if we get a domain collision between two overrides
    print "Installing feed urls override for domain "+domain
    feed_urls_override_for_domain[domain] = callback

def get_feed_urls_override_for_domain(domain):
    if domain in feed_urls_override_for_domain:
        return feed_urls_override_for_domain[domain]
    else:
        return None

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


def object_type_feed_mangler(*object_types):

    def object_type_mangler(et, account):
        from giraffe import atom
        from xml.etree import ElementTree

        feed_elem = et.getroot()
        entry_elems = feed_elem.findall(atom.ATOM_ENTRY)

        for entry_elem in entry_elems:
            object_type_elems = entry_elem.findall(atom.ACTIVITY_OBJECT_TYPE)
            if len(object_type_elems) > 0:
                continue

            for type_uri in object_types:
                object_type_elem = ElementTree.Element(atom.ACTIVITY_OBJECT_TYPE)
                object_type_elem.text = type_uri
                entry_elem.append(object_type_elem)

        return et

    return object_type_mangler


def verb_feed_mangler(*verbs):

    def verb_mangler(et, account):
        from giraffe import atom
        from xml.etree import ElementTree

        feed_elem = et.getroot()
        entry_elems = feed_elem.findall(atom.ATOM_ENTRY)

        for entry_elem in entry_elems:
            verb_elems = entry_elem.findall(atom.ACTIVITY_VERB)
            if len(verb_elems) > 0:
                continue

            for type_uri in verbs:
                verb_elem = ElementTree.Element(atom.ACTIVITY_VERB)
                verb_elem.text = type_uri
                entry_elem.append(verb_elem)

                #ElementTree.dump(entry_elem)

        return et

    return verb_mangler


def chain_feed_manglers(*manglers):
    def mangler(et, account):
        for sub_mangler in manglers:
            et = sub_mangler(et, account)
        return et

    return mangler


def conditional_feed_mangler(condition, mangler):
    def inner_mangler(et, account):
        if condition(et, account):
            et = mangler(et, account)
        return et

    return inner_mangler
