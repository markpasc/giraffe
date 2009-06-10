from django.template import Library, Node, Variable
from django.template.loader import get_template


register = Library()


class IncludeAssetByTypeNode(Node):

    template_for_type = {
        'http://activitystrea.ms/schema/1.0/bookmark': 'bookmark',
        None: 'asset',
    }

    def render(self, context):
        asset = Variable('asset').resolve(context)

        try:
            template_name = self.template_for_type[asset.object_type]
        except KeyError:
            template_name = self.template_for_type[None]

        t = get_template('library/asset/%s.html' % template_name)

        try:
            return t.render(context)
        except TemplateSyntaxError:
            if settings.TEMPLATE_DEBUG:
                raise
            return ''


@register.tag
def include_asset_by_type(parser, token):
    return IncludeAssetByTypeNode()
