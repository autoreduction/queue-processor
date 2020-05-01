import os
import sys
import django
from django.conf import settings

path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'WebApp', 'autoreduce_webapp')
view_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'WebApp', 'autoreduce_webapp', 'reduction_viewer')
print(path)
print(view_path)
sys.path.append(path)
sys.path.append(view_path)

from WebApp.autoreduce_webapp.autoreduce_webapp.settings import DATABASES, INSTALLED_APPS
settings.configure(
    DATABASES=DATABASES,
    INSTALLED_APPS=INSTALLED_APPS,
)
django.setup()

from reduction_viewer.models import Instrument

print(Instrument.objects.filter(name='GEM').first().name)

