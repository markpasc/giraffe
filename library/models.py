from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.template import Template, Context
from google.appengine.ext import db


class Query(db.Query):

    operators = {
        'exact': '=',
        None: '=',
        'lt': '<',
        'lte': '<=',
        'gt': '>',
        'gte': '>=',
        'in': 'in',
    }

    def filter(self, *args, **kwargs):
        if args:
            super(Query, self).filter(*args)

        for key, value in kwargs.iteritems():
            parts = key.split('__', 1)
            try:
                field, operator = parts
            except ValueError:
                field, operator = parts[0], None
            operator = self.operators[operator]

            query = ' '.join((field, operator))
            super(Query, self).filter(query, value)

        return self

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        if '__' not in name:
            raise AttributeError(name)
        parts = name.split('__', 2)

        try:
            field, operator, value = parts
        except ValueError:
            field, operator, value = parts[0], 'exact', parts[1]

        operator = self.operators[operator]
        query = ' '.join((field, operator))
        return self.filter(query, value)


class Model(db.Expando):

    @classmethod
    def all(cls, **kwargs):
        return Query(cls, **kwargs)


class Person(Model):

    openid = db.StringProperty()
    slug = db.StringProperty()
    name = db.StringProperty()
    # userpic?

    def blog(self):
        return Blog.all().filter(person=self)

    def actions(self):
        return Action.all().filter(person=self)

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

    object_types = {
        'video': 'http://activitystrea.ms/schema/1.0/video',
        'bookmark': 'http://activitystrea.ms/schema/1.0/bookmark',
        'post': 'http://activitystrea.ms/schema/1.0/blog-entry',
    }

    author = db.ReferenceProperty(Person)
    object_type = db.StringProperty()

    title = db.StringProperty()
    slug = db.StringProperty()
    content = db.BlobProperty()
    content_type = db.StringProperty()

    published = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

    def links(self):
        return Link.all().filter(asset=self)


class Link(Model):
    asset = db.ReferenceProperty(Asset)
    href = db.StringProperty()
    rel = db.StringProperty()
    content_type = db.StringProperty()


class Action(Model):

    verbs = {
        'post': 'http://activitystrea.ms/schema/1.0/post',
        'favorite': 'http://activitystrea.ms/schema/1.0/favorite',
    }

    person = db.ReferenceProperty(Person)
    verb = db.StringProperty()
    asset = db.ReferenceProperty(Asset)
    when = db.DateTimeProperty(auto_now_add=True)

    def byline_html(self):
        if self.verb == self.verbs['post']:
            html = "posted by %s"
        elif self.verb == self.verbs['favorite']:
            html = "saved as a favorite by %s"
        else:
            html = "acted upon by %s"
        html = html % self.person.as_html()
        return mark_safe(html)


class Blog(Model):
    person = db.ReferenceProperty(Person)
    action = db.ReferenceProperty(Action)
    posted = db.DateTimeProperty(auto_now_add=True)
