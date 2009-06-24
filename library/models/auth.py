from google.appengine.ext import db
try:
    import openid.association
except ImportError:
    import sys
    raise ValueError(repr(sys.path))

from library.models.base import Model, constants


class Association(Model):
    server_url = db.StringProperty()
    expires = db.IntegerProperty()

    handle = db.StringProperty()
    secret = db.ByteStringProperty()
    issued = db.IntegerProperty()
    lifetime = db.IntegerProperty()
    assoc_type = db.StringProperty()

    def save(self):
        self.expires = self.issued + self.lifetime
        super(Association, self).save()

    def as_openid_association(self):
        return openid.association.Association(
            handle=self.handle,
            secret=self.secret,
            issued=self.issued,
            lifetime=self.lifetime,
            assoc_type=self.assoc_type,
        )


class Squib(Model):
    server_url = db.StringProperty()
    timestamp = db.IntegerProperty()
    salt = db.StringProperty()
