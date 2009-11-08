
import django.core.management.base

from giraffe import feedmanager

class Command(django.core.management.base.NoArgsCommand):
    def handle_noargs(self, **kwargs):
        feedmanager.init()
        feedmanager.refresh_feeds()



