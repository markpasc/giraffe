from django.db import models

class TypeURI(models.Model):
    uri = models.CharField(max_length=256, unique=True)

    def __unicode__(self):
        if self.uri.startswith("http://activitystrea.ms/schema/1.0/"):
            return self.uri.replace("http://activitystrea.ms/schema/1.0/", "as:", 1)
        else:
            return self.uri

# A collection of objects that all represent the same
# thing are collected into a single bundle.
class ObjectBundle(models.Model):
    # TODO: Do we need some concept of a "primary" or "original"
    # object that we infer from the cross-posting metadata?
    def __unicode__(self):
        return str(self.pk)

class Object(models.Model):
    foreign_id = models.CharField(max_length=256, db_index = True)
    title = models.CharField(max_length=256)
    permalink_url = models.CharField(max_length=256)
    published_time = models.DateTimeField()
    object_types = models.ManyToManyField(TypeURI, related_name="objects_with_object_type")
    xml = models.TextField()
    bundle = models.ForeignKey(ObjectBundle, related_name="objects")

    def __unicode__(self):
        return self.foreign_id

class Activity(models.Model):
    foreign_id = models.CharField(max_length=256, db_index = True)
    actor = models.ForeignKey(Object, related_name="activities_with_actor")
    object = models.ForeignKey(Object, related_name="activities_with_object")
    target = models.ForeignKey(Object, related_name="activities_with_target" , null=True)
    source = models.ForeignKey(Object, related_name="activities_with_source")
    verbs = models.ManyToManyField(TypeURI, related_name="activities_with_verb")
    occurred_time = models.DateTimeField()
    xml = models.TextField()

    def __unicode__(self):
        return self.foreign_id

class Person(models.Model):
    # TODO: Do we want to foreign-key into django.contrib.auth?
    object_bundle = models.ForeignKey(ObjectBundle, related_name="people")
    display_name = models.CharField(max_length=75)

    def __unicode__(self):
        return self.display_name

class Account(models.Model):
    person = models.ForeignKey(Person, related_name="accounts")
    domain = models.CharField(max_length=75, blank=True, db_index = True)
    username = models.CharField(max_length=75, blank=True, db_index = True)
    user_id = models.CharField(max_length=75, blank=True, db_index = True)

    def __unicode__(self):
        if self.domain == "":
            # This record represents an arbitrary feed with no real "account" attached,
            # so let's just return its user_id, which is a URL.
            return self.user_id
        else:
            if self.username == "":
                # If we only have a user_id then we'll begrudgingly use that.
                return "("+self.user_id+")@"+self.domain
            else:
                # username@domain is the ideal case
                return self.username+"@"+self.domain


