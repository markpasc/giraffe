model_for_kind = dict()


def register_type(cls, kind=None):
    if kind is None:
        kind = cls.__name__.lower()

    if kind in model_for_kind:
        raise ValueError('Cannot register class %r for API as kind %r; that kind keyword is already assigned to %r'
            % (cls, kind, model_for_kind[kind]))

    model_for_kind[kind] = cls
