"""
Functionality that deals with Atom feeds containing activities and objects.
"""

import time
import datetime
import re

from lxml import etree
from giraffe import models

ATOM_PREFIX = "{http://www.w3.org/2005/Atom}"
ACTIVITY_PREFIX = "{http://activitystrea.ms/spec/1.0/}"

ATOM_FEED = ATOM_PREFIX + "feed"
ATOM_ENTRY = ATOM_PREFIX + "entry"
ATOM_ID = ATOM_PREFIX + "id"
ATOM_AUTHOR = ATOM_PREFIX + "author"
ATOM_SOURCE = ATOM_PREFIX + "source"
ATOM_TITLE = ATOM_PREFIX + "title"
ATOM_LINK = ATOM_PREFIX + "link"
ATOM_PUBLISHED = ATOM_PREFIX + "published"
ACTIVITY_SUBJECT = ACTIVITY_PREFIX + "subject"
ACTIVITY_OBJECT = ACTIVITY_PREFIX + "object"
ACTIVITY_OBJECT_TYPE = ACTIVITY_PREFIX + "object-type"
ACTIVITY_VERB = ACTIVITY_PREFIX + "verb"
ACTIVITY_TARGET = ACTIVITY_PREFIX + "target"
ACTIVITY_ACTOR = ACTIVITY_PREFIX + "actor"
POST_VERB = "http://activitystrea.ms/schema/1.0/post"

def atomactivity_to_real_activity(atom_activity):
    activity = models.Activity()

    # Turn our verb URI strings into TypeURI objects
    verb_objs = map(lambda uri : models.TypeURI.get(uri), atom_activity.verbs)

    actor = atom_entry_to_real_object(atom_activity.actor_elem)
    object = atom_entry_to_real_object(atom_activity.object_elem)
    target = atom_entry_to_real_object(atom_activity.target_elem)

    return None

def atom_entry_to_real_object(elem):

    if elem is None:
        return None

    id_elem = elem.find(ATOM_ID)
    if id_elem is None:
        return None

    id = id_elem.text

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
    title = title_elem.text

    published_elem = elem.find(ATOM_PUBLISHED)
    published_w3cdtf = published_elem.text

    object.foreign_id = id
    object.title = title
    object.published_time = _parse_date_w3cdtf(published_w3cdtf)
    for link_elem in elem.findall(ATOM_LINK):
        type = link_elem.get("type")
        rel = link_elem.get("rel")
        if rel is None or rel == "alternate":
            if type is None or type == "text/html":
                object.permalink_url = link_elem.get("href")
                break

    if object_bundle is not None:
        object_bundle.save()
        object.bundle = object_bundle

    object.save()

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

    def make_real_activity(self):
        return atomactivity_to_real_activity(self)

class AtomActivityStream:
    """
        An Activity Stream represented by an Atom feed or entry.
    """

    def __init__(self, source):
        # TODO: Also allow source to be an already-parsed etree?
        et = etree.parse(source)

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
 
       # TODO: If there's no actor specified, use atom:author instead
 
       source_elem = entry_elem.find(ATOM_SOURCE)
       if (source_elem is None): source_elem = feed_elem
 
       ret = []
 
       for object_elem in object_elems:
           activity = AtomActivity()
           activity.verbs = verbs
           activity.target_elem = target_elem
           activity.object_elem = object_elem
           activity.actor_elem = actor_elem
           activity.source_elem = source_elem
           ret.append(activity)
 
       return ret


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
            seconds = int(seconds)
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
