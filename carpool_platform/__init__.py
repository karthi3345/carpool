import re
import django.utils.cache

if not hasattr(django.utils.cache, 'cc_delim_re'):
    django.utils.cache.cc_delim_re = re.compile(r'\s*,\s*')

# Optional celery import to prevent crashing serverless environments where Celery/Redis is unconfigured
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except Exception:
    celery_app = None
    __all__ = ()
