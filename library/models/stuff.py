from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.utils.safestring import mark_safe
from google.appengine.ext import db

from library.models.base import Model, constants


class Person(Model):

    openid = db.StringProperty()
    slug = db.StringProperty()
    name = db.StringProperty()
    # userpic?

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
    )

    author = db.ReferenceProperty(Person)
    object_type = db.StringProperty()

    title = db.StringProperty()
    slug = db.StringProperty()
    content = db.BlobProperty()
    content_type = db.StringProperty()

    published = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)


class Link(Model):
    asset = db.ReferenceProperty(Asset)
    href = db.StringProperty()
    rel = db.StringProperty()
    content_type = db.StringProperty()


class Action(Model):

    verbs = constants(
        post='http://activitystrea.ms/schema/1.0/post',
        favorite='http://activitystrea.ms/schema/1.0/favorite',
    )

    person = db.ReferenceProperty(Person)
    verb = db.StringProperty()
    asset = db.ReferenceProperty(Asset)
    when = db.DateTimeProperty(auto_now_add=True)

    def byline_html(self):
        if self.verb == self.verbs.post:
            html = "posted by %s"
        elif self.verb == self.verbs.favorite:
            html = "saved as a favorite by %s"
        else:
            html = "acted upon by %s"
        html = html % self.person.as_html()
        return mark_safe(html)


class Blog(Model):
    person = db.ReferenceProperty(Person)
    action = db.ReferenceProperty(Action)
    posted = db.DateTimeProperty(auto_now_add=True)
