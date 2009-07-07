from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.utils.safestring import mark_safe
from google.appengine.ext import db

from library.models.base import Model, UtcDateTimeProperty, constants


class Person(Model):

    openid = db.StringProperty()
    slug = db.StringProperty()
    name = db.StringProperty()
    email = db.StringProperty()
    userpic = db.StringProperty()

    def get_permalink_url(self):
        if self.slug:
            return reverse('profile', kwargs={'slug': self.slug})
        return self.openid

    def as_html(self):
        t = Template('<a href="{{ person.get_permalink_url }}">{{ person.name }}</a>')
        c = Context({ 'person': self })
        html = t.render(c)
        return mark_safe(html)


class Asset(Model):

    object_types = constants(
        video='http://activitystrea.ms/schema/1.0/video',
        bookmark='http://activitystrea.ms/schema/1.0/bookmark',
        post='http://activitystrea.ms/schema/1.0/blog-entry',
        comment='http://www.bestendtimesever.com/acstrema/your-awesome-contribution',
        game='http://www.bestendtimesever.com/acstrema/pew-pew-laser-game',
    )

    name_for_object_type = object_types.inverse()

    author = db.ReferenceProperty(Person, collection_name='assets')
    object_type = db.StringProperty()

    title = db.StringProperty()
    slug = db.StringProperty()
    content = db.TextProperty()
    content_type = db.StringProperty()
    privacy_groups = db.StringListProperty()

    in_reply_to = db.SelfReferenceProperty(collection_name='replies')
    thread = db.SelfReferenceProperty(collection_name='thread_members')

    published = UtcDateTimeProperty(auto_now_add=True)
    updated = UtcDateTimeProperty(auto_now=True)

    def get_permalink_url(self):
        if self.slug is not None:
            return reverse('asset', kwargs={'slug': self.slug})
        return reverse('asset', kwargs={'slug': self.key()})

    def content_as_html(self):
        template_for_type = {
            'text/markdown': "{% load markup %}{{ asset.content|markdown }}",
            'text/html': "{% autoescape off %}{{ asset.content }}{% endautoescape %}",
            None: "{% asset.content %}",
        }

        code = template_for_type.get(self.content_type, template_for_type[None])
        t = Template(code)
        c = Context({ 'asset': self })
        html = t.render(c)
        return mark_safe(html)

    def save(self):
        if self.object_type is None:
            self.object_type = self.object_types.post

        if not self.privacy_groups:
            self.privacy_groups = ["public"]

        super(Asset, self).save()

    def save_and_post(self):
        self.save()

        # Make an action.
        act = Action(person=self.author, asset=self, verb=Action.verbs.post,
            when=self.published, privacy_groups=self.privacy_groups)
        act.save()


class Link(Model):
    asset = db.ReferenceProperty(Asset, collection_name='links')
    href = db.StringProperty()
    rel = db.StringProperty()
    content_type = db.StringProperty()


class Action(Model):

    verbs = constants(
        post='http://activitystrea.ms/schema/1.0/post',
        favorite='http://activitystrea.ms/schema/1.0/favorite',
        comment='http://www.bestendtimesever.com/acstrema/you-awesomely-contributing',
    )

    person = db.ReferenceProperty(Person, collection_name='actions')
    verb = db.StringProperty()
    asset = db.ReferenceProperty(Asset, collection_name='actions')
    when = UtcDateTimeProperty(auto_now_add=True)

    privacy_groups = db.StringListProperty()

    def byline_html(self):
        if self.verb == self.verbs.post:
            html = "posted by %s"
        elif self.verb == self.verbs.favorite:
            html = "saved as a favorite by %s"
        else:
            html = "acted upon by %s"
        html = html % self.person.as_html()
        return mark_safe(html)
