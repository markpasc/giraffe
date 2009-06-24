from google.appengine.ext import db


model_for_kind = {}

def model_with_kind(kind):
    try:
        return model_for_kind[kind.lower()]
    except KeyError:
        raise ValueError("No such model with kind %r" % kind)


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


class ModelMeta(db.Expando.__metaclass__):

    def __new__(cls, name, bases, attr):
        newcls = super(ModelMeta, cls).__new__(cls, name, bases, attr)
        if name != 'Model':
            model_for_kind[newcls.kind().lower()] = newcls
        return newcls


class Model(db.Expando):

    __metaclass__ = ModelMeta

    @classmethod
    def all(cls, **kwargs):
        return Query(cls, **kwargs)

    def all_properties(self):
        return self.properties().keys() + self.dynamic_properties()

    def as_data(self):
        data = dict([(k, getattr(self, k)) for k in self.all_properties()])

        try:
            data['key'] = str(self.key())
        except db.NotSavedError:
            pass

        return data
