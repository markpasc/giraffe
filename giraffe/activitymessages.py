"""
Functionality for rendering natural language sentences that describe activities.
"""


from giraffe import typeuriselector
from giraffe import typehandler
from xml.etree import ElementTree
from xml.sax.saxutils import escape, quoteattr
import string
import re


MB_PREFIX = "{http://activitystrea.ms/messagebundles}"
MB_MESSAGE_BUNDLE = MB_PREFIX + "message-bundle";
MB_URI_ALIAS = MB_PREFIX + "uri-alias";
MB_CONTEXT = MB_PREFIX + "context";
MB_MESSAGE = MB_PREFIX + "message";

MB_SELECTION_ATTRS = ("verb", "actor-type", "object-type", "target-type", "source-type")


VARIABLE_REGEX = re.compile(r'\{(\*?)(\w+(?:\.\w+)*)\}')


class MessageSet:

    def __init__(self):
        self.messages = {}

    def import_message_bundle(self, et):
        _import_messages_from_bundle(et, self)

    @staticmethod
    def with_defaults(cls):
        from os.path import join, dirname
        ret = cls()
        defaults_file = file(join(dirname(__file__), 'defaultmessages.xml'))
        ret.import_message_bundle(ElementTree.parse(defaults_file))
        return ret

    def get_plain_message_for_activity(self, activity):
        def expander(value):
            return repr(value)
        return self.get_message_for_activity(activity, expander)

    def get_html_message_for_activity(self, activity):
        def expander(value, is_html):

            permalinkUrl = None

            parts = []

            if isinstance(value, dict):
                if "permalinkUrl" in value:
                    permalinkUrl = value["permalinkUrl"]

                if "displayName" in value and value["displayName"]:
                    value = value["displayName"]
                else:
                    value = "(no title)"

            if permalinkUrl:
                parts.append("<a href=%s>" % quoteattr(permalinkUrl))

            if is_html:
                parts.append(value)
            else:
                parts.append(escape(value))

            if permalinkUrl:
                parts.append("</a>")

            return ''.join(parts)

        return self.get_message_for_activity(activity, expander)

    def get_message_for_activity(self, activity, expander):

        for selector in _make_selection_tuple_iterator_for_activity(self, activity):
            if selector in self.messages:
                message_template = self.messages[selector]

                vars = {}
                vars["target"] = typehandler.get_object_as_dict(activity.target)
                vars["object"] = typehandler.get_object_as_dict(activity.object)
                vars["actor"] = typehandler.get_object_as_dict(activity.actor)
                vars["source"] = typehandler.get_object_as_dict(activity.source)

                # We track if any of the variables fail to expand, and if
                # so move on to the next message to avoid returning an
                # incomplete message.
                # We use a list here to trick python's stupid semi-lexical-scoping
                # into letting us write a value out here.
                missed = [False]

                def replace(matchobj):

                    if matchobj.group(1) == "*":
                        is_html = True
                    else:
                        is_html = False

                    current = vars
                    for chunk in matchobj.group(2).split("."):
                        try:
                            current = current[chunk]
                        except KeyError:
                            pass
                        except TypeError:
                            pass

                        if current is None:
                            missed[0] = True
                            return ""

                    return expander(current, is_html=is_html)

                result = VARIABLE_REGEX.sub(replace, message_template)

                if not missed[0]:
                    return result

        # If we fell out here then there was no matching message,
        # either because the verbs and object types aren't known
        # or because the message template tried to substitute
        # a variable that's not available for this activity.
        return None


def _import_messages_from_bundle(et, message_set):

    messages = message_set.messages

    # First we need to figure out what aliases we're using for this bundle
    aliases = {}
    alias_elems = et.findall(MB_URI_ALIAS)

    for alias_elem in alias_elems:
        aliases[alias_elem.get("alias")] = alias_elem.get("prefix")

    # Now we traverse the tree
    context_stack = []

    root_frame = {}

    for attr in MB_SELECTION_ATTRS:
        root_frame[attr] = None

    # Actor actually defaults to *, because the common case is that
    # we don't care what type it is, and all activities have an actor anyway.
    root_frame["actor-type"] = "*"

    context_stack.append(root_frame)

    elems = et.getroot().getchildren()

    for elem in elems:
        if elem.tag in (MB_CONTEXT, MB_MESSAGE):
            _import_messages_from_elem(elem, messages, context_stack, aliases)

def _import_messages_from_elem(elem, messages, context_stack, aliases):

    if elem.tag == MB_CONTEXT:

        context_frame = {}
        previous_frame = context_stack[-1]

        for attr in MB_SELECTION_ATTRS:
            default = previous_frame[attr]
            context_frame[attr] = _expand_uri(elem.get(attr, default), aliases)

        context_stack.append(context_frame)

        for elem in elem.getchildren():
            _import_messages_from_elem(elem, messages, context_stack, aliases)

        context_stack.pop()

    elif elem.tag == MB_MESSAGE:

        context_frame = {}
        previous_frame = context_stack[-1]

        message = string.strip(elem.text)

        for attr in MB_SELECTION_ATTRS:
            default = previous_frame[attr]
            context_frame[attr] = _expand_uri(elem.get(attr, default), aliases)

            # Any placeholder used in a message that is not explicitly given a type by
            # this point defaults to *.
            if context_frame[attr] is None and attr != "verb":
                var = "{%s}" % attr[:-5]
                if message.find(var) != -1:
                    context_frame[attr] = "*"

        c = context_frame
        selector_tuple = tuple(map(lambda attr : context_frame[attr], MB_SELECTION_ATTRS))

        messages[selector_tuple] = message


def _expand_uri(uri, aliases):
    if uri is None or len(uri) < 1:
        return uri

    if uri[0] == "{":
        (pre, sep, post) = uri.partition("}")
        alias = pre[1:]
        suffix = post
        return aliases[alias]+suffix
    else:
        return uri


def _make_selection_tuple_iterator_for_activity(message_set, activity):

    verbs = typeuriselector.sort_types_by_derivedness(activity.verb_uris)
    verbs.append("*")
    object_types = [ "*" ]
    target_types = [ None ]
    actor_types = [ "*" ]
    source_types = [ None ]

    if activity.object is not None:
        object_types = typeuriselector.sort_types_by_derivedness(activity.object.object_type_uris)
        object_types.append("*")
    if activity.target is not None:
        target_types = typeuriselector.sort_types_by_derivedness(activity.target.object_type_uris)
        target_types.append("*")
        source_types.append(None)
    if activity.actor is not None:
        actor_types = typeuriselector.sort_types_by_derivedness(activity.actor.object_type_uris)
        actor_types.append("*")
    if activity.source is not None:
        source_types = typeuriselector.sort_types_by_derivedness(activity.source.object_type_uris)
        source_types.append("*")
        source_types.append(None)

    for actor_type in actor_types:
        for source_type in source_types:
            for target_type in target_types:
                for verb in verbs:
                    for object_type in object_types:
                        yield(verb, actor_type, object_type, target_type, source_type)


