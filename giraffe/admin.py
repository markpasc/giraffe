
from django.contrib import admin
from giraffe import models

class ObjectAdmin(admin.ModelAdmin):
    date_hierarchy = "published_time"
    list_display = [ "foreign_id", "title", "permalink_url", "published_time", "bundle" ]
    list_filter = [ "object_types" ]
    raw_id_fields = [ "bundle" ]
    search_fields = [ "title" ]

class ActivityAdmin(admin.ModelAdmin):
    date_hierarchy = "occurred_time"
    list_display = [ "foreign_id", "actor", "object", "target", "occurred_time" ]
    list_filter = [ "verbs" ]

class ObjectBundleAdmin(admin.ModelAdmin):
    list_display = [ "pk" ]

class TypeURIAdmin(admin.ModelAdmin):
    list_display = [ "uri" ]

admin.site.register(models.TypeURI, TypeURIAdmin)
admin.site.register(models.ObjectBundle)
admin.site.register(models.Object, ObjectAdmin)
admin.site.register(models.Activity, ActivityAdmin)
admin.site.register(models.Person)
admin.site.register(models.Account)



