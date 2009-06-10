from google.appengine.ext import db


class Person(db.Expando):
    openid = db.StringProperty()


class Asset(db.Expando):
    author = db.ReferenceProperty(Person)
    title = db.StringProperty()
    slug = db.StringProperty()
    content = db.BlobProperty()
    published = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)


class Action(db.Expando):
    who = db.ReferenceProperty(Person)
    verb = db.StringProperty()
    what = db.ReferenceProperty(Asset)
    when = db.DateTimeProperty(auto_now_add=True)
