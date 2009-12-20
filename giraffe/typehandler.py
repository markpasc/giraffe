
from xml.etree import ElementTree
import json

from giraffe import models
from giraffe import atom
from giraffe import activitystreams


handler_for_object_type = {}

DEFAULT_HANDLER = None


def get_object_as_atom(object, element_name = None):
    if object.data_format == "A":
        elem = ElementTree.XML(object.data)
        if element_name is not None:
            elem.tag = element_name
        return elem
    else:
        # Need to convert from dict
        dict = json.loads(object.data)
        object_types = filter_and_sort_object_type_list(object.object_type_uris)

        if element_name is None:
            element_name = atom.ACTIVITY_OBJECT

        elem = ElementTree.Element(element_name)

        id_elem = ElementTree.Element(atom.ATOM_ID)
        id_elem.text = object.foreign_id
        elem.append(id_elem)

        title_elem = ElementTree.Element(atom.ATOM_TITLE)
        title_elem.text = object.display_name
        elem.append(title_elem)

        permalink_elem = ElementTree.Element(atom.ATOM_LINK, { "href": object.permalink_url, "rel": "alternate", "type": "text/html" })
        elem.append(permalink_elem)

        # FIXME: Also need to put the published time in here

        for object_type in object_types:
            object_type_elem = ElementTree.Element(atom.ACTIVITY_OBJECT_TYPE)
            object_type_elem.text = object_type
            elem.append(object_type_elem)

        # Give each handler in turn a chance to add things to the Atom element
        for object_type in object_types:
            handler = handler_for_object_type[object_type]
            handler.populate_atom_from_dict(dict, elem)

        return elem
        

def get_object_as_dict(object):
    if object.data_format == "J":
        dict = json.loads(object.data)
        return dict
    else:
        # Need to convert from Atom
        elem = ElementTree.XML(object.data)
        object_types = filter_and_sort_object_type_list(object.object_type_uris)

        dict = {}
        
        dict["id"] = object.foreign_id
        dict["displayName"] = object.display_name
        dict["permalinkUrl"] = object.permalink_url
        dict["objectTypes"] = object_types

        # FIXME: Also need to put the published time in here

        # Give each handler in turn a chance to add things to the Atom element
        for object_type in object_types:
            handler = handler_for_object_type[object_type]
            handler.populate_dict_from_atom(elem, dict)

        return dict


def filter_and_sort_object_type_list(object_types):
    object_types = filter(lambda uri: uri in handler_for_object_type, object_types)

    from giraffe import typeuriselector
    return typeuriselector.sort_types_by_derivedness(object_types)


def register_object_type_handler(type_uri, handler):
    handler_for_object_type[type_uri] = handler


def register_dummy_object_type_handler(type_uri):
    """
    Registers an object type handler for the given type uri with no implementation.

    This is useful for derived types that have a defined type URI but don't actually add any new properties.
    """
    handler_for_object_type[type_uri] = DEFAULT_HANDLER


def map_values_from_elem(dict, elem, mappings):
    for key_name in mappings:
        value = elem.findtext(mappings[key_name])
        if value is not None:
            dict[key_name] = value
    

def map_lists_from_elem(dict, elem, mappings):
    for key_name in mappings:
        dict[key_name] = {}
        values = elem.findall(mappings[key_name])
        for value_elem in values:
            dict[key_name].append(value_elem.text)
    

def map_link_from_elem(dict, elem, key, rel):
    for link_elem in elem.findall(atom.ATOM_LINK):
        if link_elem.get("rel") == rel:
            dict[key] = {}
            dict[key]["type"] = link_elem.get("type")
            dict[key]["href"] = link_elem.get("href")
            dict[key]["width"] = link_elem.get("{http://purl.org/syndication/atommedia}width")
            dict[key]["height"] = link_elem.get("{http://purl.org/syndication/atommedia}height")
            break
    

def map_links_from_elem(dict, elem, key, rel):
    dict[key] = []
    ret = dict[key]
    for link_elem in elem.findall(atom.ATOM_LINK):
        if link_elem.get("rel") == rel:
            item = {}
            item["type"] = link_elem.get("type")
            item["href"] = link_elem.get("href")
            width = link_elem.get("{http://purl.org/syndication/atommedia}width")
            height = link_elem.get("{http://purl.org/syndication/atommedia}height")
            if width: item["width"] = width
            if height: item["height"] = height
            ret.append(item)
    

class TypeHandler(object):
    """
    Abstract base class for type handlers.
    """

    def populate_dict_from_atom(self, object_elem, object_dict):
        # Default implementation is to do nothing;
        # what we've been given in object_dict is fine.
        pass

    def populate_atom_from_dict(self, object_dict, object_elem):
        # Default implementation is to do nothing;
        # what we've been given in object_elem is fine.
        pass
        
DEFAULT_HANDLER = TypeHandler()


class ArticleTypeHandler(TypeHandler):

    def populate_dict_from_atom(self, object_elem, object_dict):
        mappings = {
            'content': atom.ATOM_CONTENT,
        }
        map_values_from_elem(object_dict, object_elem, mappings)

    def populate_atom_from_dict(self, object_dict, object_elem):
        if "content" in object_dict:
            content_elem = object_elem.find(atom.ATOM_CONTENT)
            if content_elem is None:
                content_elem = ElementTree.Element(atom.ATOM_CONTENT)
                object_elem.append(content_elem)
            content_elem.text = object_dict["content"]


class NoteTypeHandler(TypeHandler):

    def populate_dict_from_atom(self, object_elem, object_dict):
        mappings = {
            'content': atom.ATOM_CONTENT,
        }
        map_values_from_elem(object_dict, object_elem, mappings)

    def populate_atom_from_dict(self, object_dict, object_elem):
        if "content" in object_dict:
            content_elem = object_elem.find(atom.ATOM_CONTENT)
            if content_elem is None:
                content_elem = ElementTree.Element(atom.ATOM_CONTENT)
                object_elem.append(content_elem)
            content_elem.text = object_dict["content"]


class PersonTypeHandler(TypeHandler):

    def populate_dict_from_atom(self, object_elem, object_dict):
        map_links_from_elem(object_dict, object_elem, "avatars", "avatar")

    def populate_atom_from_dict(self, object_dict, object_elem):
        if avatars in object_dict:
            for avatar_link in avatars:
                link_elem = ElementTree.Element(atom.ATOM_LINK, {'rel':'avatar'})
                for key in ('href', 'type'):
                    if key in avatar_link: link_elem.set(key, avatar_link[key])
                for key in ('width', 'height'):
                    attr_name = "{http://purl.org/syndication/atommedia}%s" % key
                    if key in avatar_link: link_elem.set(attr_name, avatar_link[key])
                object_elem.append(link_elem)


class SongTypeHandler(TypeHandler):

    def populate_dict_from_atom(self, object_elem, object_dict):
        mappings = {
            'artistName': atom.ATOM_AUTHOR+"/"+atom.ATOM_NAME,
            'artistUrl': atom.ATOM_AUTHOR+"/"+atom.ATOM_URI,
        }
        map_values_from_elem(object_dict, object_elem, mappings)

    def populate_atom_from_dict(self, object_dict, object_elem):
        if "artistName" in object_dict or "artistUrl" in object_dict:
            author_elem = ElementTree.Element(atom.ATOM_AUTHOR)
            if "artistName" in object_dict:
                name_elem = ElementTree.Element(atom.ATOM_NAME)
                name_elem.text = object_dict["artistName"]
                author_elem.append(name_elem)
            if "artistUrl" in object_dict:
                uri_elem = ElementTree.Element(atom.ATOM_URI)
                uri_elem.text = object_dict["artistUrl"]
                author_elem.append(uri_elem)
            object_elem.append(author_elem)


class PhotoTypeHandler(TypeHandler):

    def populate_dict_from_atom(self, object_elem, object_dict):
        map_links_from_elem(object_dict, object_elem, "fullImages", "enclosure")
        map_links_from_elem(object_dict, object_elem, "thumbnails", "preview")

    def populate_atom_from_dict(self, object_dict, object_elem):
        if avatars in object_dict:
            for avatar_link in avatars:
                link_elem = ElementTree.Element(atom.ATOM_LINK, {'rel':'avatar'})
                for key in ('href', 'type'):
                    if key in avatar_link: link_elem.set(key, avatar_link[key])
                for key in ('width', 'height'):
                    attr_name = "{http://purl.org/syndication/atommedia}%s" % key
                    if key in avatar_link: link_elem.set(attr_name, avatar_link[key])
                object_elem.append(link_elem)


_tu = activitystreams.type_uri

register_object_type_handler(_tu("article"), ArticleTypeHandler())
register_object_type_handler(_tu("blog-entry"), ArticleTypeHandler())
register_object_type_handler(_tu("note"), NoteTypeHandler())
register_object_type_handler(_tu("person"), PersonTypeHandler())
register_object_type_handler(_tu("photo"), PhotoTypeHandler())
register_object_type_handler(_tu("song"), SongTypeHandler())

