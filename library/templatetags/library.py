from datetime import datetime, timedelta

from django.conf import settings
from django.template import Library, Node, Variable, TemplateSyntaxError, TemplateDoesNotExist, VariableDoesNotExist
from django.template.loader import get_template


register = Library()


class IncludeAssetByTypeNode(Node):

    def __init__(self, format='post'):
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

    return then.strftime("at %Y-%m-%d %H:%M")


@register.filter
def atomdate(when):
    return when.replace(microsecond=0).isoformat() + 'Z'
