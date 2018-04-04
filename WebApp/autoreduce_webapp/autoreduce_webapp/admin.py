"""
Initialise admin pages
"""
from django.contrib import admin
# pylint: disable=relative-import
from models import UserCache, InstrumentCache, ExperimentCache

admin.site.register(UserCache)
admin.site.register(InstrumentCache)
admin.site.register(ExperimentCache)
