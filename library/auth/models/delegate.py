from google.appengine.ext import db
from random import choice

from library.models import Model, constants, Person


class Consumer(Model):
    keyid = db.StringProperty()
    secret = db.StringProperty()
    name = db.StringProperty()
    owner = db.ReferenceProperty(Person)

    def save(self):
        if self.keyid is None:
            self.keyid = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(20)])
        if self.secret is None:
            self.secret = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(30)])
        super(Consumer, self).save()


class Token(Model):
    keyid = db.StringProperty()
    secret = db.StringProperty()
    consumer = db.ReferenceProperty(Consumer)
    person = db.ReferenceProperty(Person)
    issued = db.DateTimeProperty(auto_now_add=True)

    def save(self):
        if self.keyid is None:
            self.keyid = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(20)])
        if self.secret is None:
            self.secret = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(30)])
        super(Token, self).save()


class Squib(Model):
    consumer = db.ReferenceProperty(Consumer)
    timestamp = db.DateTimeProperty(auto_now_add=True)
    value = db.ByteStringProperty()

    api_type = 'oauth_squib'
