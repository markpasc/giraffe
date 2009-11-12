
# This is just a temporary development tool to make it easier
# to seed the accounts table with real data.
# It's not written very well.

import cgi
import urlparse

import django.core.management.base

from giraffe import models
from giraffe import socialgraphapi


def import_node(node, person):
    account = uri_to_account(node.uri)

    print "processing "+node.uri

    account.person = person

    dupe_account = existing_account(account)
    if dupe_account is not None:
        print "already have it!"
        return dupe_account

    attributes = node.attributes()

    if "pk_is" in attributes:
        pk_account = uri_to_account(attributes["pk_is"])
        pk_account.person = person
        pk_account_dupe = existing_account(pk_account)
        if pk_account_dupe is not None and pk_account_dupe.username == "":
            pk_account_dupe.username = account.username
            pk_account_dupe.save()
            return pk_account_dupe

    if "ident_is" in attributes:
        ident_account = uri_to_account(attributes["ident_is"])
        ident_account.person = person
        ident_account_dupe = existing_account(ident_account)
        if ident_account_dupe is not None and ident_account_dupe.user_id == "":
            ident_account_dupe.user_id = account.user_id
            ident_account_dupe.save()
            return ident_account_dupe

    account.save()

    for claimed_node in node.claimed_nodes():
        import_node(claimed_node, person)

    return account

def existing_account(account):
    existing_accounts = []

    # Do we already have an account for this?
    if account.username != "":
        print "looking for an account with domain %s, username %s" % (account.domain, account.username)
        try:
            existing_accounts = models.Account.objects.filter(domain = account.domain, username = account.username, person = account.person)
        except:
            pass
    elif account.user_id != "":
        print "looking for an account with domain %s, user_id %s" % (account.domain, account.user_id)
        try:
            existing_accounts = models.Account.objects.filter(domain = account.domain, user_id = account.user_id, person = account.person)
        except:
            pass

    if len(existing_accounts) > 0:
        return existing_accounts[0]
    else:
        return None

def uri_to_account(uri):
    account = models.Account()

    if uri.startswith("sgn:"):
        # urlparse parses sgn: URIs wrong, so we trick
        # it into doing the right thing by changing
        # the scheme.
        uri = uri.replace("sgn:", "http:", 1)
        parts = urlparse.urlparse(uri)
        domain = parts.netloc
        query = parts.query
        query_vars = cgi.parse_qs(query)

        account.domain = domain

        if "pk" in query_vars:
            account.user_id = query_vars["pk"][0]

        if "ident" in query_vars:
            account.username = query_vars["ident"][0]

    else:
        account.domain = ""
        account.username = uri
        account.user_id = ""

    return account

class Command(django.core.management.base.BaseCommand):
    def handle(self, *args, **kwargs):
        uri = args[0]
        person_pk = args[1]

        person = models.Person.objects.filter(pk = person_pk)[0]

        node = socialgraphapi.lookup_node(uri)

        import_node(node, person)


