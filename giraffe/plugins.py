import logging


plugins_initialized = False


def init():
    """
    Initialize plugin functionality from other applications.
    
    Searches all of the installed apps for a module called 'giraffe' and, if it's present, imports it.

    The best place to run this is at the start of your urls.py, before you declare any URLs.
    """

    global plugins_initialized

    logging.debug("Loading plugins")

    if plugins_initialized:
        return
    
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        modname = '.'.join((app, "giraffe_plugins"))
        try:
            __import__(modname)
            logging.debug("Loaded plugins from " + modname)
        except ImportError, exc:
            # No giraffe plugins in this module. Oh well.
            continue

    plugins_initialized = True
