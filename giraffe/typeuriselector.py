
"""
A registry for the heirarchical type URI namespace, and a mechanism
to select the most specific out of a selection of types.
"""

types = {}

def register_toplevel_type(uri):
    if uri in types:
        raise ConflictError()
    types[uri] = 0

def register_derived_type(new_uri, base_uri):
    if base_uri in types:
        if new_uri in types:
            # We already have both types.
            raise ConflictError()
        else:
            types[new_uri] = types[base_uri] + 1
    else:
        if new_uri in types:
            # We've registered these backwards, so
            # we need to put base_uri behind new_uri
            types[base_uri] = types[new_uri] - 1
        else:
            # Let's register the base type first.
            register_toplevel_type[base_uri]



class ConflictError(Exception):
    pass
