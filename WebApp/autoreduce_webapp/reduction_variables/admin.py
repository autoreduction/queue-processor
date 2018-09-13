"""
Register models variables here
"""
from django.contrib import admin
from reduction_variables.models import InstrumentVariable, RunVariable

# Register your models here.
admin.site.register(InstrumentVariable)
admin.site.register(RunVariable)
