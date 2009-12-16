
type_uris = {}

def type_uri(keyword):
    if keyword in type_uris:
        return type_uris[keyword]
    else:
        type_uris[keyword] = "http://activitystrea.ms/schema/1.0/%s" % keyword
        return type_uris[keyword]

