from django.db import models
from settings import LOG_FILE, LOG_LEVEL, BASE_DIR
import logging
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_viewer.models import Status

'''
    Provide a list field type to be used by models
    See: http://cramer.io/2008/08/08/custom-fields-in-django/
'''
class SeparatedValuesField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value: return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_db_prep_value(self, value, connection, prepared=False):
        if not value: return
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.token.join([unicode(s) for s in value])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


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