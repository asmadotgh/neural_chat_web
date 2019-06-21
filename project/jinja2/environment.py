from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from jinja2 import Environment
from jinja2_pluralize import pluralize_dj
import simplejson
from django.conf import settings

def cachebreak():
    return "?c=" + settings.STARTUP_TIMESTAMP


def environment(**options):
    env = Environment(**options)
    env.filters.update({
        'pluralize': pluralize_dj,
        'json': simplejson.dumps,
    })
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'list': list,
        'cachebreak': cachebreak,
    })
    return env
