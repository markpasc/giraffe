"""
Functionality that deals with Atom feeds containing activities and objects.
"""

import time
import datetime
import re

from xml.etree import ElementTree
from giraffe import models

ATOM_PREFIX = "{http://www.w3.org/2005/Atom}"
ACTIVITY_PREFIX = "{http://activitystrea.ms/spec/1.0/}"

ATOM_FEED = ATOM_PREFIX + "feed"
ATOM_ENTRY = ATOM_PREFIX + "entry"
ATOM_ID = ATOM_PREFIX + "id"
ATOM_AUTHOR = ATOM_PREFIX + "author"
ATOM_SOURCE = ATOM_PREFIX + "source"
ATOM_TITLE = ATOM_PREFIX + "title"
ATOM_CONTENT = ATOM_PREFIX + "content"
ATOM_LINK = ATOM_PREFIX + "link"
ATOM_PUBLISHED = ATOM_PREFIX + "published"
ATOM_NAME = ATOM_PREFIX + "name"
ATOM_URI = ATOM_PREFIX + "uri"
ACTIVITY_SUBJECT = ACTIVITY_PREFIX + "subject"
ACTIVITY_OBJECT = ACTIVITY_PREFIX + "object"
ACTIVITY_OBJECT_TYPE = ACTIVITY_PREFIX + "object-type"
ACTIVITY_VERB = ACTIVITY_PREFIX + "verb"
ACTIVITY_TARGET = ACTIVITY_PREFIX + "target"
ACTIVITY_ACTOR = ACTIVITY_PREFIX + "actor"
POST_VERB = "http://activitystrea.ms/schema/1.0/post"

def atomactivity_to_real_activity(atom_activity):

    # Turn our verb URI strings into TypeURI objects
    verb_objs = map(lambda uri : models.TypeURI.get(uri), atom_activity.verbs)

    actor = atom_entry_to_real_object(atom_activity.actor_elem)
    object = atom_entry_to_real_object(atom_activity.object_elem)
    target = atom_entry_to_real_object(atom_activity.target_elem)
    source = atom_entry_to_real_object(atom_activity.source_elem)

    # An activity that doesn't have an actor or an object isn't interesting to us.
    if actor is None or object is None:
        return None

    actor_bundle = None
    object_bundle = None
    target_bundle = None
    source_bundle = None

    if actor is not None:
        actor_bundle = actor.bundle
    if object is not None:
        object_bundle = object.bundle
    if target is not None:
        target_bundle = target.bundle
    if source is not None:
        source_bundle = source.bundle

    # Do we already have this activity in our database?
    matching_activities = models.Activity.objects.filter(
        actor_bundle=actor_bundle,
        object_bundle=object_bundle,
        target_bundle=target_bundle,
        source_bundle=source_bundle,
        occurred_time=atom_activity.occurred_time,
    )

    activity = None
    for possible_activity in matching_activities:
        verb_uris = possible_activity.verb_uris
        if atom_activity.verbs == verb_uris:
            # We have a match!
            activity = possible_activity
            return activity

    if activity is None:
        activity = models.Activity()

    activity.actor = actor
    activity.object = object
    activity.target = target
    activity.source = source
    activity.actor_bundle = actor_bundle
    activity.object_bundle = object_bundle
    activity.target_bundle = target_bundle
    activity.source_bundle = source_bundle
    activity.occurred_time = atom_activity.occurred_time

    activity.save()

    activity.verbs.clear()
    for v_o in verb_objs:
        activity.verbs.add(v_o)

    return activity

def atom_entry_to_real_object(elem):

    if elem is None:
        return None

    id_elem = elem.find(ATOM_ID)

    permalink_url = ""
    for link_elem in elem.findall(ATOM_LINK):
        type = link_elem.get("type")
        rel = link_elem.get("rel")
        if rel is None or rel == "alternate":
            if type is None or type == "text/html":
                permalink_url = link_elem.get("href")
                break

    id = None
    if id_elem is not None:
        id = id_elem.text
    else:
        # Fall back on the permalink URL as an id
        id = permalink_url

    # If we still don't have something useful to use as an id,
    # bail out.
    if not id:
        return None

    # Do we already have this object?
    object_bundle = None
    try:
        object = models.Object.by_foreign_id(id)
    except models.Object.DoesNotExist:
        object = models.Object()
        object_bundle = models.ObjectBundle()

    object_types = map(lambda elem : elem.text, elem.findall(ACTIVITY_OBJECT_TYPE))
    object_type_objs = map(lambda uri : models.TypeURI.get(uri), object_types)

    title_elem = elem.find(ATOM_TITLE)
    if title_elem is None:
        title = ""
    else:
        title = title_elem.text

    if title is None:
        title = ""

    published_elem = elem.find(ATOM_PUBLISHED)
    if published_elem is None:
        published_datetime = object.published_time
    else:
        published_w3cdtf = published_elem.text
        published_datetime = _parse_date_w3cdtf(published_w3cdtf)

    if published_datetime is None:
        # Fall back on it being published now, which is
        # probably wrong but at least it'll sort in
        # more-or-less the right order.
        published_datetime = datetime.datetime.now()

    object.foreign_id = id
    object.display_name = title
    object.published_time = published_datetime
    object.permalink_url = permalink_url

    object.data_format = "A"
    object.data = ElementTree.tostring(elem)

    if object_bundle is not None:
        object_bundle.save()
        object.bundle = object_bundle

    object.save()

    object.object_types.clear()
    for ot_o in object_type_objs:
        object.object_types.add(ot_o)

    return object

class AtomActivity:
    """
        An Activity constructed from Atom input.
    """

    verbs = None
    object_elem = None
    target_elem = None
    actor_elem = None
    source_elem = None
    occurred_time = None

    def make_real_activity(self):
        return atomactivity_to_real_activity(self)

class AtomActivityStream:
    """
        An Activity Stream represented by an Atom feed or entry.
    """

    def __init__(self, et):
        # TODO: Also allow source to be an already-parsed etree?

        ret = []

        self.feed_elem = et.getroot()
        self.activities = ret
        self.subject_elem = None

        feed_elem = self.feed_elem

        if (self.feed_elem.tag == ATOM_FEED):
            self.subject_elem = feed_elem.find(ACTIVITY_SUBJECT)
            entry_elems = feed_elem.findall(ATOM_ENTRY)
            for entry_elem in entry_elems:
                ret.extend(self._activities_from_atom_entry(entry_elem))
        elif (self.feed_elem.tag == ATOM_ENTRY):
            # We actually don't have a feed elem, then.
            entry_elem = feed_elem
            self.feed_elem = None
            ret.extend(self._activities_from_atom_entry(entry_elem))
        else:
            # TODO: Support RSS?
            pass

    def _activities_from_atom_entry(self, entry_elem):
       object_elems = entry_elem.findall(ACTIVITY_OBJECT)
 
       if len(object_elems) == 0:
           # The entry itself is the object here
           object_elems = [ entry_elem ]

       feed_subject_elem = self.subject_elem
       feed_elem = self.feed_elem
 
       verbs = map(lambda elem : elem.text, entry_elem.findall(ACTIVITY_VERB))
 
       if (len(verbs) == 0): verbs = [ POST_VERB ]
 
       target_elem = entry_elem.find(ACTIVITY_TARGET)
 
       # Get the id of the feed subject, if there is one
       subject_id = None
       if feed_subject_elem is not None:
           subject_id_elem = feed_subject_elem.find(ATOM_ID)
           if subject_id_elem is not None: subject_id = subject_id_elem.text
 
       # If the id of the actor matches the id of the subject, use the subject
       # in place of the object.
       actor_elem = entry_elem.find(ACTIVITY_ACTOR)
       if actor_elem is not None:
           actor_id_elem = actor_elem.find(ATOM_ID)
           if actor_id_elem is not None:
               actor_id = actor_id_elem.text
               if actor_id == subject_id: actor_elem = feed_subject_elem
 
       if actor_elem is None:
           # Synthesize an actor from the author.
           author_elem = entry_elem.find(ATOM_AUTHOR)
           if author_elem is None:
               author_elem = feed_elem.find(ATOM_AUTHOR)
           if author_elem is not None:
               author_id_elem = author_elem.find(ATOM_ID)
               author_id = None
               # Atom deson't actually specify id as a valid child of author,
               # but if it's present it's probably better than what we'd
               # synthesize below.
               if author_id_elem is not None:
                   author_id = author_id_elem.text

               feed_id_elem = feed_elem.find(ATOM_ID)
               feed_id = ""
               if feed_id_elem is not None:
                   feed_id = feed_id_elem.text

               author_name_elem = author_elem.find(ATOM_NAME)
               if author_name_elem is not None:
                   author_name = author_name_elem.text
               else:
                   author_name = ""
               
               author_uri_elem = author_elem.find(ATOM_URI)
               if author_uri_elem is not None:
                   author_uri = author_uri_elem.text
               else:
                   author_uri = ""
               
               actor_elem = ElementTree.Element(ACTIVITY_ACTOR)
               
               actor_title_elem = ElementTree.Element(ATOM_TITLE)
               actor_title_elem.text = author_name
               actor_elem.append(actor_title_elem)

               if author_uri != "":
                   actor_permalink_elem = ElementTree.Element(ATOM_LINK, {"href":author_uri, "type":"text/html", "rel":"alternate"})
                   actor_elem.append(actor_permalink_elem)

               if author_id is None:
                   author_id = "x-giraffe-fake-actor:%s@%s@%s" % (author_name, author_uri, feed_id)

               actor_id_elem = ElementTree.Element(ATOM_ID)
               actor_id_elem.text = author_id
               actor_elem.append(actor_id_elem)

       source_elem = entry_elem.find(ATOM_SOURCE)
       if (source_elem is None): source_elem = feed_elem

       published_elem = entry_elem.find(ATOM_PUBLISHED)
       occurred_time = None
       if published_elem is not None:
           occurred_time = _parse_date_w3cdtf(published_elem.text)

       if occurred_time is None:
           # Can't do anything sane with an activity that has no published time
           return []
 
       ret = []
 
       for object_elem in object_elems:
           activity = AtomActivity()
           activity.verbs = verbs
           activity.target_elem = target_elem
           activity.object_elem = object_elem
           activity.actor_elem = actor_elem
           activity.source_elem = source_elem
           activity.occurred_time = occurred_time
           ret.append(activity)
 
       return ret


def urlpoller_callback(account):
    def callback(url, result):
        print "Got an activity feed update for "+str(account)+" at "+url
        # "result" is a sufficiently file-like object that
        # we can just pass it right into ElementTree as-is.
        et = ElementTree.parse(result)

        from giraffe import accounts
        mangler = accounts.get_feed_mangler_for_domain(account.domain)

        et = mangler(et, account)

        activity_stream = AtomActivityStream(et)

        # FIXME: If activity_stream has a subject, create a link between
        # the account and the subject.

        for atom_activity in activity_stream.activities:
            activity = atom_activity.make_real_activity()
            if activity is not None:
                activity.source_account = account
                activity.source_person = account.person
                if account.person.personal_activity_stream:
                    account.person.personal_activity_stream.activities.add(activity)
                activity.save()
    return callback


# This is pilfered from Universal Feed Parser.
def _parse_date_w3cdtf(dateString):
    def __extract_date(m):
        year = int(m.group('year'))
        if year < 100:
            year = 100 * int(time.gmtime()[0] / 100) + int(year)
        if year < 1000:
            return 0, 0, 0
        julian = m.group('julian')
        if julian:
            julian = int(julian)
            month = julian / 30 + 1
            day = julian % 30 + 1
            jday = None
            while jday != julian:
                t = time.mktime((year, month, day, 0, 0, 0, 0, 0, 0))
                jday = time.gmtime(t)[-2]
                diff = abs(jday - julian)
                if jday > julian:
                    if diff < day:
                        day = day - diff
                    else:
                        month = month - 1
                        day = 31
                elif jday < julian:
                    if day + diff < 28:
                       day = day + diff
                    else:
                        month = month + 1
            return year, month, day
        month = m.group('month')
        day = 1
        if month is None:
            month = 1
        else:
            month = int(month)
            day = m.group('day')
            if day:
                day = int(day)
            else:
                day = 1
        return year, month, day

    def __extract_time(m):
        if not m:
            return 0, 0, 0
        hours = m.group('hours')
        if not hours:
            return 0, 0, 0
        hours = int(hours)
        minutes = int(m.group('minutes'))
        seconds = m.group('seconds')
        if seconds:
            seconds = int(float(seconds))
        else:
            seconds = 0
        return hours, minutes, seconds

    def __extract_tzd(m):
        '''Return the Time Zone Designator as an offset in seconds from UTC.'''
        if not m:
            return 0
        tzd = m.group('tzd')
        if not tzd:
            return 0
        if tzd == 'Z':
            return 0
        hours = int(m.group('tzdhours'))
        minutes = m.group('tzdminutes')
        if minutes:
            minutes = int(minutes)
        else:
            minutes = 0
        offset = (hours*60 + minutes) * 60
        if tzd[0] == '+':
            return -offset
        return offset

    __date_re = ('(?P<year>\d\d\d\d)'
                 '(?:(?P<dsep>-|)'
                 '(?:(?P<julian>\d\d\d)'
                 '|(?P<month>\d\d)(?:(?P=dsep)(?P<day>\d\d))?))?')
    __tzd_re = '(?P<tzd>[-+](?P<tzdhours>\d\d)(?::?(?P<tzdminutes>\d\d))|Z)'
    __tzd_rx = re.compile(__tzd_re)
    __time_re = ('(?P<hours>\d\d)(?P<tsep>:|)(?P<minutes>\d\d)'
                 '(?:(?P=tsep)(?P<seconds>\d\d(?:[.,]\d+)?))?'
                 + __tzd_re)
    __datetime_re = '%s(?:T%s)?' % (__date_re, __time_re)
    __datetime_rx = re.compile(__datetime_re)
    m = __datetime_rx.match(dateString)
    if (m is None) or (m.group() != dateString): return
    gmt = __extract_date(m) + __extract_time(m) + (0, 0, 0)
    if gmt[0] == 0: return
    return datetime.datetime.utcfromtimestamp(time.mktime(gmt) + __extract_tzd(m) - time.timezone)
