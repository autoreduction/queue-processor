import os.path
from reduction_viewer.models import Instrument
from autoreduce_webapp.settings import REDUCTION_DIRECTORY

def deactivate_invalid_instruments(fn):
    """
    Function decorator that checks the reduction script for all active instruments 
    and deactivates any that cannot be found
    """
    def request_processor(request, *args, **kws):
        instruments = Instrument.objects.filter(is_active=True)
        for instrument in instruments:
            reduction_path = os.path.join(REDUCTION_DIRECTORY % (instrument.name), 'reduce.py')
            if not os.path.isfile(reduction_path):
                logging.warn("Could not find runduction file: %s" % reduction_path)
                instrument.is_active = False
                instrument.save()

        return fn(request, *args, **kws)
    return request_processor