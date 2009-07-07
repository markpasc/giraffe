class Conduit(object):

    def lookup(self, id):
        raise NotImplementedError()

    def search(self, **kwargs):
        raise NotImplementedError()
