"""
Initialise admin pages
"""
from django.contrib import admin

from WebApp.autoreduce_webapp.autoreduce_webapp.models import (UserCache,
                                                               InstrumentCache,
                                                               ExperimentCache)

admin.site.register(UserCache)
admin.site.register(InstrumentCache)
admin.site.register(ExperimentCache)
