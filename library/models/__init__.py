from library.models.base import *
from library.models.auth import *
from library.models.stuff import *


import logging

from django.conf import settings

for zone, level in getattr(settings, 'LOG_LEVELS', {}).items():
    log = logging.getLogger(zone)
    log.setLevel(level)
    logging.info('Set log %s to level %s', zone,
        logging.getLevelName(level))
