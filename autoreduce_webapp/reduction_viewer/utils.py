import logging, os, sys
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, BASE_DIR
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
from django.db import models
from reduction_viewer.models import Instrument, Status

class StatusUtils():
    def _get_status(status_value):
        status, created = Status.objects.get_or_create(value=status_value)
        if created:
            logging.warn("%s status was not found, created it." % status_value)
        return status

    def get_error():
        return self.__get_status("Error")

    def get_completed():
        return self.__get_status("Completed")

    def get_processing():
        return self.__get_status("Processing")

    def get_queued():
        return self.__get_status("Queued")
            
class InstrumentUtils():
    def get_instrument(instrument_name):
        instrument, created = Instrument.objects.get_or_create(name__iexact=instrument_name)
        if created:
            logging.warn("%s instrument was not found, created it." % instrument_name)
        return instrument