from datetime import datetime


object_encoders = list()


def register(cls, encoder):
    object_encoders.append((cls, encoder))


register(datetime, 'isoformat')


def encoder(obj):
    for cls, encoder in object_encoders:
        if not isinstance(obj, cls):
            continue

        if not callable(encoder):
            try:
                encoder = getattr(obj, encoder)
            except AttributeError:
                raise ValueError('Encoder %r for class %s.%s is neither callable nor an attribute of %s instance %r'
                    % (encoder, cls.__module__, cls.__name__,
                       type(obj).__name__, obj))
        return encoder(obj)

    raise TypeError("%s instance %r is not json serializable"
        % (type(obj).__name__, obj))
