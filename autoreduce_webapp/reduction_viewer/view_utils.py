import os.path
from reduction_viewer.models import Instrument
from autoreduce_webapp.settings import REDUCTION_SCRIPT_BASE

def deactivate_invalid_instruments(fn):
    def request_processor(request, *args, **kws):
        instruments = Instrument.objects.filter(is_active=True)
        for instrument in instruments:
            if not os.path.isfile(os.path.join(REDUCTION_SCRIPT_BASE, instrument.name, 'reduce.py')):
                instrument.is_active = False

        return fn(request, *args, **kws)
    return request_processor