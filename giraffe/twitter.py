"""
Twitter's Atom feeds are sufficiently strange that we need some custom
code to process them. That custom code lives in here.
"""

from xml.etree import ElementTree
import re

from giraffe import atom


def urlpoller_callback(account):
    def callback(url, result):
        print "Got Twitter poll result for %s which is for account %s" % (url, str(account))

        et = ElementTree.parse(result)
        feed_elem = et.getroot()

        entry_elems = feed_elem.findall(atom.ATOM_ENTRY)

        # Twitter doesn't provide a person object with an id, so we
        # synthesize one that follows the same naming scheme
        # Twitter currently uses for entry ids.
        actor_elem = ElementTree.Element(atom.ACTIVITY_ACTOR)
        actor_id = "tag:twitter.com,2007:http://twitter.com/%s" % account.username
        actor_id_elem = ElementTree.Element(atom.ATOM_ID)
        actor_id_elem.text = actor_id
        actor_title_elem = ElementTree.Element(atom.ATOM_TITLE)
        actor_title_elem.text = account.username
        actor_link_elem = ElementTree.Element(atom.ATOM_LINK, { "href": account.profile_url(), "rel": "alternate", "type": "text/html" })
        actor_elem.append(actor_id_elem)
        actor_elem.append(actor_title_elem)
        actor_elem.append(actor_link_elem)

        for entry_elem in entry_elems:
            title_elem = entry_elem.find(atom.ATOM_TITLE)
            content_elem = entry_elem.find(atom.ATOM_CONTENT)
            parts = content_elem.text.split(": ", 1)
            text = parts[1]

            text = re.sub("https?://[\S]+", lambda match : "<a href=\"%s\">%s</a>" % match.group(0, 0), text)
            text = re.sub("#(\w+)", lambda match : "<a href=\"http://twitter.com/search?q=%%23%s\">%s</a>" % match.group(1, 0), text)
            text = re.sub("@(\w+)", lambda match : "@<a href=\"http://twitter.com/%s\">%s</a>" % match.group(1, 1), text)

            title_elem.text = ""
            content_elem.text = text

            published_elem = entry_elem.find(atom.ATOM_PUBLISHED)
            published_w3cdtf = published_elem.text
            published_datetime = atom._parse_date_w3cdtf(published_w3cdtf)

            object_type_elem = ElementTree.Element(atom.ACTIVITY_OBJECT_TYPE)
            object_type_elem.text = "http://activitystrea.ms/schema/1.0/note"
            entry_elem.append(object_type_elem)

            atom_activity = atom.AtomActivity()
            atom_activity.verbs = [ "http://activitystrea.ms/schema/1.0/post" ]
            atom_activity.object_elem = entry_elem
            atom_activity.actor_elem = actor_elem
            atom_activity.source_elem = feed_elem
            atom_activity.occurred_time = published_datetime

            activity = atom_activity.make_real_activity()

            if activity is not None:
                activity.source_account = account
                activity.source_person = account.person
                activity.save()

    return callback

