from django.db import models

from giraffe import accounts


class TypeURI(models.Model):

    uri = models.CharField(max_length=256, unique=True)

    def __unicode__(self):
        if self.uri.startswith("http://activitystrea.ms/schema/1.0/"):
            return self.uri.replace("http://activitystrea.ms/schema/1.0/", "as:", 1)
        else:
            return self.uri

    @classmethod
    def get(cls, uri):

        # Does the thing already exist?
        objs = cls.objects.filter(uri = uri)

        if len(objs) > 0:
            return objs[0]

        # Otherwise, we need to create it.
        try:
            obj = cls(uri = uri)
            obj.save()
            return obj
        except ValidationError:
            # Someone else created it in the mean time
            return cls.objects.filter(uri = uri)[0]


class ObjectBundle(models.Model):

    """A collection of objects that all represent the same thing."""

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
    target = models.ForeignKey(Object, related_name="activities_with_target", null=True)
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
            # so let's just return its username, which is a URL.
            return self.username
        else:
            if self.username == "":
                # If we only have a user_id then we'll begrudgingly use that.
                return "("+self.user_id+")@"+self.domain
            else:
                # username@domain is the ideal case
                return self.username+"@"+self.domain

    def handler(self):
        return accounts.AccountHandler.for_domain(self.domain)

    def display_username(self):
        return self.handler().display_username_for_account(self)

    def activity_feed_urls(self):
        return self.handler().activity_feed_urls_for_account(self)

    def provider_name(self):
        return self.handler().provider_name()

    def profile_url(self):
        return self.handler().profile_url_for_account(self)

    def profile_link_html(self):
        profile_url = self.profile_url()
        if profile_url is not None:
            return "<a href='%s'>%s</a>" % (profile_url, profile_url)
        else:
            return None
    profile_link_html.allow_tags = True


class PolledURL(models.Model):

    url = models.CharField(max_length=256, db_index = True, unique = True)
    notifications_enabled = models.BooleanField()
    last_fetch_time = models.DateTimeField(null=True, db_index = True)
    last_fetch_status = models.IntegerField(null=True, blank=True)
    last_fetch_etag = models.CharField(max_length=256, blank=True)

    def __unicode__(self):
        return self.url
