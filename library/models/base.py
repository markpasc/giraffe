import logging

from google.appengine.ext import db


log = logging.getLogger('library.models.base')


model_for_kind = {}

def model_with_kind(kind):
    try:
        return model_for_kind[kind.lower()]
    except KeyError:
        raise ValueError("No such model with kind %r" % kind)


class Constants(object):
    class Immutable(Exception):
        pass

    def __init__(self, *args, **kwargs):
        for arg in args:
            self.__dict__.update(arg)
        self.__dict__.update(kwargs)
    def __getitem__(self, key):
        return self.__dict__[key]
    def __setitem__(self, key, value):
        raise self.Immutable()
    def __delitem__(self, key):
        raise self.Immutable()
    def __setattr__(self, key, value):
        raise self.Immutable()
    def __delattr__(self, key):
        raise self.Immutable()

constants = Constants


class Query(db.Query):

    operators = constants({
        'exact': '=',
        None: '=',
        'lt': '<',
        'lte': '<=',
        'gt': '>',
        'gte': '>=',
        'in': 'in',
    })

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

    def __repr__(self):
        clauses = list()
        for clause in self.__query_sets:
            clauses.extend(clause.items())
        return "<Query for %s where %s in %s order>" % (self._model_class.__name__,
            ', '.join([' '.join((k, str(v))) for k,v in clauses]),
            ', '.join(self.__orderings))


class ModelMeta(db.Expando.__metaclass__):

    def __new__(cls, name, bases, attr):
        newcls = super(ModelMeta, cls).__new__(cls, name, bases, attr)

        # Register in the models set.
        if name != 'Model':
            model_for_kind[newcls.kind().lower()] = newcls

        return newcls


class Model(db.Expando):

    __metaclass__ = ModelMeta

    @classmethod
    def all(cls, **kwargs):
        return Query(cls, **kwargs)

    @classmethod
    def get(cls, *args, **kwargs):
        if not kwargs:
            return super(Model, cls).get(*args)

        all_kwargs = dict()
        try:
            all_kwargs['keys_only'] = kwargs.pop('keys_only')
        except KeyError:
            pass

        q = cls.all(**all_kwargs).filter(**kwargs)
        try:
            obj = q[0]
        except IndexError:
            return
        else:
            return obj

    def all_properties(self):
        return self.properties().keys() + self.dynamic_properties()

    def as_data(self):
        data = dict([(k, getattr(self, k)) for k in self.all_properties()])

        try:
            data['key'] = str(self.key())
        except db.NotSavedError:
            pass

        return data
