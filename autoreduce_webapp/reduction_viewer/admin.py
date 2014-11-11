from django.contrib import admin
from models import *

# Register your models here.
admin.site.register(Instrument)
admin.site.register(Experiment)
admin.site.register(Status)
admin.site.register(ReductionRun)
admin.site.register(DataLocation)
admin.site.register(ReductionLocation)
admin.site.register(Setting)
admin.site.register(Notification)