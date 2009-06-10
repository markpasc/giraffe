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
        q = self

        if args:
            q = super(Query, q).filter(*args)

        for key, value in kwargs.iteritems():
            parts = key.split('__', 1)
            try:
                field, operator = parts
            except ValueError:
                field, operator = parts[0], None
            operator = self.operators[operator]

            query = ' '.join((field, operator))
            q = super(Query, self).filter(query, value)

        return q

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


class Asset(Model):
    author = db.ReferenceProperty(Person)
    object_type = db.StringProperty()

    title = db.StringProperty()
    slug = db.StringProperty()
    content = db.BlobProperty()
    category = db.CategoryProperty()

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
    who = db.ReferenceProperty(Person)
    verb = db.StringProperty()
    what = db.ReferenceProperty(Asset)
    when = db.DateTimeProperty(auto_now_add=True)
