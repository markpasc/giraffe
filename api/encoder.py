from datetime import datetime


object_encoders = list()


def register(cls, encoder):
    object_encoders.append((cls, encoder))


register(datetime, lambda dt: dt.isoformat())


def encoder(obj):
    for cls, encoder in object_encoders:
        if not isinstance(obj, cls):
            continue

        return encoder(obj)

    raise TypeError("%s instance %r is not json serializable"
        % (type(obj).__name__, obj))
