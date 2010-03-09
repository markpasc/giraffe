from xml.etree import ElementTree

from django.http import HttpResponse
import simplejson as json

from giraffe import atom, models


def activity_stream_atom_feed(request, stream_key=None, title=""):
    stream = models.ActivityStream.objects.get(key=stream_key)
    if not stream:
        raise LookupError("There is no stream with the key "+stream_key)

    response = HttpResponse()

    activities = stream.activities.order_by('-occurred_time').all()[:25]
    et = atom.render_feed_from_activity_list(activities, title=title)

    response["content-type"] = "application/atom+xml"
    response.content = ElementTree.tostring(et.getroot())

    return response


def activity_stream_json(request, stream_key=None, title=""):
    stream = models.ActivityStream.objects.get(key=stream_key)
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
