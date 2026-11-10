"""
WSGI config for carpool_platform project.
"""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path so Vercel serverless runtime can locate apps
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carpool_platform.settings')

application = get_wsgi_application()

# Alias app for Vercel WSGI entry point
app = application
