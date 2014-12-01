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
            reduction_path = REDUCTION_DIRECTORY % (instrument.name)
            if not os.path.isfile(os.path.join(reduction_path, 'reduce.py')):
                instrument.is_active = False
                instrument.save()

        return fn(request, *args, **kws)
    return request_processor