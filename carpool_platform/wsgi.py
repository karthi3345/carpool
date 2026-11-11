"""
WSGI config for carpool_platform project.
"""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path so Vercel serverless runtime can locate apps
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import traceback

try:
    from django.core.wsgi import get_wsgi_application
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carpool_platform.settings')
    _django_app = get_wsgi_application()

    def application(environ, start_response):
        try:
            return _django_app(environ, start_response)
        except Exception:
            err_trace = traceback.format_exc()
            body = f"Django Runtime Exception:\n\n{err_trace}".encode('utf-8')
            start_response("500 Internal Server Error", [
                ("Content-Type", "text/plain"),
                ("Content-Length", str(len(body)))
            ])
            return [body]

except Exception:
    _init_err = traceback.format_exc()
    def application(environ, start_response):
        body = f"Django WSGI Startup Fatal Error:\n\n{_init_err}".encode('utf-8')
        start_response("500 Internal Server Error", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body)))
        ])
        return [body]

# Alias app for Vercel WSGI entry point
app = application
