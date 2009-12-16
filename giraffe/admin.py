
from django.contrib import admin
from giraffe import models

class ObjectAdmin(admin.ModelAdmin):
    date_hierarchy = "published_time"
    list_display = [ "foreign_id", "display_name", "permalink_url", "published_time", "bundle" ]
    list_filter = [ "object_types" ]
    raw_id_fields = [ "bundle" ]
    search_fields = [ "display_name" ]

class ActivityAdmin(admin.ModelAdmin):
    date_hierarchy = "occurred_time"
    list_display = [ "pk", "source_person", "object", "target", "occurred_time" ]
    list_filter = [ "verbs", "source_person", "activity_streams" ]

class ObjectBundleAdmin(admin.ModelAdmin):
    list_display = [ "pk" ]

class TypeURIAdmin(admin.ModelAdmin):
    list_display = [ "uri" ]

class PolledURLAdmin(admin.ModelAdmin):
    list_display = [ "url", "notifications_enabled", "last_fetch_time", "last_fetch_status" ]
    list_filter = [ "notifications_enabled" ]
    search_fields = [ "url" ]

class AccountAdmin(admin.ModelAdmin):
    list_display = [ "person", "__unicode__", "provider_name", "profile_link_html" ]
    list_display_links = [ "__unicode__" ]
    search_fields = [ "username", "user_id", "domain" ]
    list_filter = [ "person" ]

class ObjectToAccountAdmin(admin.ModelAdmin):
    list_display = [ "object", "account" ]

class ActivityStreamAdmin(admin.ModelAdmin):
    list_display = [ "pk", "key" ]

admin.site.register(models.TypeURI, TypeURIAdmin)
admin.site.register(models.ObjectBundle)
admin.site.register(models.Object, ObjectAdmin)
admin.site.register(models.Activity, ActivityAdmin)
admin.site.register(models.Person)
admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.PolledURL, PolledURLAdmin)
admin.site.register(models.ObjectToAccount, ObjectToAccountAdmin)
admin.site.register(models.ActivityStream, ActivityStreamAdmin)



