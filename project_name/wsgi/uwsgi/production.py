"""
WSGI config for {{ project_name }} project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import os
import site

site.addsitedir('/home/django/sites/{{ project_name }}/lib/python3.4/site-packages')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")

# This is where you load celery
#import djcelery
#djcelery.setup_loader()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
