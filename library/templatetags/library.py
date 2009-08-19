from __future__ import absolute_import

import cgi
from datetime import datetime, timedelta
from functools import wraps
from xml.sax.saxutils import escape

from django.conf import settings
from django.template import Library, Node, Variable, Context, TemplateSyntaxError, TemplateDoesNotExist, VariableDoesNotExist
from django.template.defaultfilters import stringfilter
from django.template.defaulttags import url, URLNode
from django.template.loader import get_template

from library.models.stuff import Asset


register = Library()


def is_safe(fn):
    fn.is_safe = True
    return fn


class IncludeAssetByTypeNode(Node):

    def __init__(self, format=None):
        if format is None:
            format = 'post'
        self.format = format

    def render(self, context):
        asset = Variable('asset').resolve(context)

        try:
            template_name = asset.name_for_object_type[asset.object_type]
        except KeyError:
            template_name = 'asset'

        try:
            t = get_template('library/asset/%s/%s.html' % (self.format, template_name))
        except TemplateDoesNotExist:
            try:
                t = get_template('library/asset/%s/asset.html' % (self.format,))
            except TemplateDoesNotExist:
                raise ValueError("Asset format template %r does not exist" % (self.format,))

        try:
            return t.render(context)
        except TemplateSyntaxError:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''


@register.tag
def include_asset_by_type(parser, token):
    bits = token.split_contents()
    if len(bits) > 1:
        return IncludeAssetByTypeNode(bits[1])
    return IncludeAssetByTypeNode()


class AbsoluteURLNode(URLNode):

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        return context['request'].build_absolute_uri(output)


@register.tag
def absoluteurl(parser, token):
    nodelist = parser.parse(('endabsoluteurl',))
    parser.delete_first_token()
    return AbsoluteURLNode(nodelist)


@register.filter
def fuzzysince(then):
    now = datetime.utcnow()
    if then < now:
        since = now - then
        if since <= timedelta(minutes=2):
            return "just now"
        if since <= timedelta(minutes=75):
            return "%d minutes ago" % (since.seconds / 60,)
        if since <= timedelta(hours=12):
            return "%d hours ago" % (since.seconds / 3600,)
    elif now < then:
        until = then - now
        if until <= timedelta(minutes=2):
            return "now"
        if until <= timedelta(minutes=75):
            return "%d minutes from now" % (until.seconds / 60,)
        if until <= timedelta(hours=6):
            return "%d hours from now" % (until.seconds / 3600,)
    else:
        return "right now"

    return then.strftime("at %H:%M on %d %b %Y")


@register.filter
def atomdate(when):
    return when.replace(microsecond=0).isoformat() + 'Z'


@register.filter
@is_safe
@stringfilter
def escapexml(what):
    return escape(what)


from HTMLParser import HTMLParser

def when_no_object(fn):
    @wraps(fn)
    def do_when_no_object(self, *args, **kwargs):
        if self.object is None:
            return fn(self, *args, **kwargs)
    return do_when_no_object

class AssetizingParser(HTMLParser):

    def reset(self):
        HTMLParser.reset(self)
        self.content = list()
        self.object = None

    def handle_starttag(self, tag, attrs):
        if self.object is not None:
            if tag == 'param':
                param = dict(attrs)
                self.object[param.get('name')] = param.get('value')
            return

        if tag == 'object':
            params = dict(attrs)
            if params.get('type') == 'text/x-asset':
                self.object = dict()
                return

        self.content.extend(('<', tag))
        if attrs:
            self.content.append(' ')
            for attr in attrs:
                self.content.extend((attr[0], '="', cgi.escape(attr[1], True), '" '))
        self.content.append('>')

    def handle_endtag(self, tag):
        if self.object is not None:
            if tag == 'object':
                asset = Asset.get(self.object['key'])
                context = Context({'asset': asset})

                node = IncludeAssetByTypeNode(self.object.get('format'))
                html = node.render(context)

                self.content.append(html)
                self.object = None
            return

        self.content.extend(('</', tag, '>'))

    @when_no_object
    def handle_data(self, data):
        self.content.append(data)

    @when_no_object
    def handle_charref(self, name):
        self.content.extend(('&#', name, ';'))

    @when_no_object
    def handle_entityref(self, name):
        self.content.extend(('&', name, ';'))

    @when_no_object
    def handle_comment(self, data):
        self.content.extend(('<!--', data, '-->'))

    def result(self):
        return ''.join(self.content)

    @classmethod
    def assetize(cls, text):
        self = cls()
        self.feed(text)
        self.close()
        return self.result()


@register.filter
@is_safe
@stringfilter
def assetize(what):
    # Parse html, replacing the text/x-asset objects with other subtemplates.
    return AssetizingParser.assetize(what)
