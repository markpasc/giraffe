
import django.core.management.base

import json

from giraffe import plugins
from giraffe import models
from giraffe import typehandler


class Command(django.core.management.base.BaseCommand):
    def handle(self, *args, **kwargs):
        plugins.init()
        object_id = args[0]
        object = models.Object.objects.get(id=object_id)
        dict = typehandler.get_object_as_dict(object)
        print json.dumps(dict, indent=4)
