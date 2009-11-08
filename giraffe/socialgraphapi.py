
"""
Functions for interacting with Google's Social Graph API.
"""

import urllib2
import urllib
import simplejson as json

SGAPI_LOOKUP = "http://socialgraph.apis.google.com/lookup"

class SocialGraphNode:

    nodes = None
    uri = None

    def __init__(self, nodes, uri):
        self.nodes = nodes
        self.uri = uri

    def json_obj(self):
        if self.uri in self.nodes:
            return self.nodes[self.uri]
        else:
            return { "attributes": {}, "claimed_nodes": [] }

    def attributes(self):
        return self.json_obj()["attributes"]

    def claimed_nodes(self):
        return map(lambda uri : SocialGraphNode(self.nodes, uri), self.json_obj()["claimed_nodes"])

    def __unicode__(self):
        return self.uri

def lookup_node(uri):
    nodes = lookup_nodes([uri])
    return nodes[uri]

def lookup_nodes(uris):
    ret = {}

    params = [
        ("fme", "1"),
        ("pretty", "0"),
        ("sgn", "1"),
        ("q", ",".join(uris))
    ]
    qs = urllib.urlencode(params)
    url = "?".join([SGAPI_LOOKUP, qs])

    result = urllib2.urlopen(url)
    struct = json.load(result)

    nodes = struct["nodes"]
    canonical_mapping = struct["canonical_mapping"]

    for uri in uris:
        canon_uri = canonical_mapping[uri]
        ret[uri] = SocialGraphNode(nodes, canon_uri)

    return ret

