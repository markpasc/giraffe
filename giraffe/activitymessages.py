"""
Functionality for rendering natural language sentences that describe activities.
"""


from xml.etree import ElementTree
import string


MB_PREFIX = "{http://activitystrea.ms/messagebundles}"
MB_MESSAGE_BUNDLE = MB_PREFIX + "message-bundle";
MB_URI_ALIAS = MB_PREFIX + "uri-alias";
MB_CONTEXT = MB_PREFIX + "context";
MB_MESSAGE = MB_PREFIX + "message";

MB_SELECTION_ATTRS = ("verb", "actor-type", "object-type", "target-type", "source-type")

class MessageSet:

    def __init__(self):
        self.messages = {}

    def import_message_bundle(self, et):
        _import_messages_from_bundle(et, self.messages)


def _import_messages_from_bundle(et, messages):

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

