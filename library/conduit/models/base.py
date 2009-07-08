class Conduit(object):

    provides = ()

    @classmethod
    def lookup(cls, id):
        raise NotImplementedError()

    @classmethod
    def search(cls, **kwargs):
        raise NotImplementedError()


class Result(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def save_asset(self):
        raise NotImplementedError()
