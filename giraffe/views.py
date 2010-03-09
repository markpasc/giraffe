from os.path import dirname, join
from xml.etree import ElementTree

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
import simplejson as json

from giraffe.activitymessages import MessageSet
from giraffe import atom
from giraffe.models import ActivityStream


mset = MessageSet.with_defaults()


def activity_stream(request, stream_key=None, template_name='giraffe/stream.html'):
    stream = ActivityStream.objects.get(key=stream_key)
    if not stream:
        raise Http404

    # TODO: page
    activities = stream.activities.all()[:25]

    for activity in activities:
        activity.html = mset.get_html_message_for_activity(activity)

    return render_to_response(template_name, {
        'stream': stream,
        'activities': activities,
    }, context_instance=RequestContext(request))


def activity_stream_atom_feed(request, stream_key=None, title=""):
    stream = ActivityStream.objects.get(key=stream_key)
    if not stream:
        raise LookupError("There is no stream with the key "+stream_key)

    response = HttpResponse()

    activities = stream.activities.order_by('-occurred_time').all()[:25]
    et = atom.render_feed_from_activity_list(activities, title=title)

    response["content-type"] = "application/atom+xml"
    response.content = ElementTree.tostring(et.getroot())

    return response


def activity_stream_json(request, stream_key=None, title=""):
    stream = ActivityStream.objects.get(key=stream_key)
    if not stream:
        raise LookupError("There is no stream with the key "+stream_key)

    response = HttpResponse()
    response["content-type"] = "application/json"

    ret = {}

    ret["title"] = title
    json_activities = []
    ret["entries"] = json_activities

    activities = stream.activities.order_by('-occurred_time').all()[:25]

    for activity in activities:
        json_activity = {}

        json_verbs = []
        json_activity["verbs"] = json_verbs
        json_activity["postedTime"] = activity.occurred_time.isoformat()

        from giraffe import typehandler
        object = activity.object
        if object:
            json_activity["object"] = typehandler.get_object_as_dict(object)
        target = activity.target
        if target:
            json_activity["target"] = typehandler.get_object_as_dict(target)
        actor = activity.actor
        if actor:
            json_activity["actor"] = typehandler.get_object_as_dict(actor)
        source = activity.source
        if source:
            json_activity["source"] = typehandler.get_object_as_dict(source)

        for verb_uri_obj in activity.verbs.all():
            json_verbs.append(verb_uri_obj.uri)

        json_activities.append(json_activity)

    response.content = json.dumps(ret)

    return response
