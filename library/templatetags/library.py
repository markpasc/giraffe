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
