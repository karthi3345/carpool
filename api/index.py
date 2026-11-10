import os
import sys
from pathlib import Path

# Set up project root in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "carpool_platform.settings")

from django.core.wsgi import get_wsgi_application

# Vercel serverless functions hook into 'app'
app = get_wsgi_application()
