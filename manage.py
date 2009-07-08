#!/usr/bin/env python

import os
import sys

from appengine_django import InstallAppengineHelperForDjango, PARENT_DIR
InstallAppengineHelperForDjango()

from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

for zipfile in ('openid.zip', 'remoteobjects.zip'):
    zip_path = os.path.join(PARENT_DIR, zipfile)
    if zip_path not in sys.path:
        sys.path.insert(1, zip_path)

if __name__ == "__main__":
    execute_manager(settings)
