
import django.core.management.base

from giraffe import plugins
from giraffe import feedmanager

class Command(django.core.management.base.NoArgsCommand):
    def handle_noargs(self, **kwargs):
        plugins.init()
        feedmanager.init()
        feedmanager.refresh_feeds()



