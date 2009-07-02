from google.appengine.ext import db

from library.models import Model, constants, Person


class Consumer(Model):
    id = db.StringProperty()
    secret = db.StringProperty()
    return_url = db.StringProperty()


class Token(Model):
    id = db.ByteStringProperty()
    secret = db.ByteStringProperty()
    consumer = db.ReferenceProperty(Consumer)
    person = db.ReferenceProperty(Person)
    issued = db.DateTimeProperty(auto_now_add=True)

    def save(self):
        if self.id is None:
            self.id = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(20)])
        if self.secret is None:
            self.secret = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(30)])
        super(RequestToken, self).save()


class Squib(Model):
    consumer = db.ReferenceProperty(Consumer)
    timestamp = db.DateTimeProperty(auto_now_add=True)
    value = db.ByteStringProperty()
