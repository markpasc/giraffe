import inspect
import re
import sys

from django.conf import settings
from django.conf.urls.defaults import *


setting_name_re = re.compile(r'^[A-Z_]+$')


def app_module(app, name):
    """Finds whether the given app contains a module by the given name.

    If the specified `app` contains a module named `name`, this method returns
    that combined name. For example, to detect that an app named ``kittens``
    contains an ``urls`` module, one would call ``app_module('kittens',
    'urls')``, which would return the string ``'kittens.urls'``. If no such
    module exists, this module returns ``None``.

    If the requested module does exist, it will be imported as a side effect
    of calling this function. Having been imported, a module that does exist
    will then be available in the ``sys.modules`` dictionary.

    """
    modname = '.'.join((app, name))
    try:
        __import__(modname)
    except ImportError:
        return None
    else:
        return modname


def urls_for_apps(exclude=None):
    """Collects urlconfs for all installed apps that have them.

    Append this function to your project urlconf to automatically include the
    patterns from all your enabled apps' urlconfs thus::

        import reusable

        urlpatterns = patterns(...)  # extra non-app patterns

        urlpatterns += reusable.urls_for_apps()

    All app urlconfs are included at the root in the order they are supplied
    in `INSTALLED_APPS`; therefore if several apps try to claim a particular
    path for their views, the one listed first in `INSTALLED_APPS` will serve
    that URL path. To disambiguate, include the apps in your urlconf
    explicitly at non-root paths.

    To exclude apps from inclusion in this automatically constructed set (for
    example, if you aren't using that app's views, or are including them
    yourself in the project urlconf), provide as an `exclude` parameter the
    names of the apps not to include.

    """
    if exclude is None:
        exclude = ()

    return patterns('',
        *[(r'^', include(app_module(app, 'urls'))) for app in settings.INSTALLED_APPS
            if app not in exclude and app_module(app, 'urls') is not None]
    )


def include_app_settings(skip_local=False):
    """Injects all Django settings from installed apps' `settings` modules
    into the caller's context.

    Call this function at the end of your `settings` module thus::

        import reusable
        reusable.include_app_settings()

    All settings in the `settings` modules of packages named in the
    ``INSTALLED_APPS`` setting are included; if an app has no such package,
    that app is skipped (but if loading the exception causes a `SyntaxError`
    or other exception, the exception is raised). Only variables named in
    ``CONSTANT_CASE`` are considered settings and included from apps' settings
    modules. Apps' `settings` modules can use and modify the settings loaded
    so far by loading them through the normal ``from django.conf import
    settings`` statement.

    When called normally, settings are also loaded from the ``local_settings``
    module, if any. Pass ``True`` for the `skip_local` argument to prevent use
    of the ``local_settings`` module.

    """
    caller_locals = inspect.currentframe().f_back.f_locals

    included_apps = set()
    def modules():
        """Generate a list of modules from which to install settings.

        This list includes the `settings` modules of all `INSTALLED_APPS`,
        even if one of the apps' settings modules modifies the list. The list
        of modules will also end with `local_settings`, unless
        `include_app_settings()` was asked not to include them.

        """
        done = False
        while not done:
            done = True  # guess we're done
            for app in caller_locals['INSTALLED_APPS']:
                if app in included_apps:
                    continue
                try:
                    mod_name = app_module(app, 'settings')
                    if mod_name is None:
                        continue
                    yield mod_name
                finally:
                    included_apps.add(app)
                    done = False  # but if we add a new one we're not

        if not skip_local:
            # TODO: account for DJANGO_SETTINGS_MODULE?
            try:
                __import__('local_settings')
            except ImportError:
                pass
            else:
                yield 'local_settings'

    for mod_name in modules():
        app_settings = sys.modules[mod_name]

        # Copy all those settings into our caller's locals.
        for maybe_setting in dir(app_settings):
            if setting_name_re.match(maybe_setting):
                caller_locals[maybe_setting] = getattr(app_settings, maybe_setting)
