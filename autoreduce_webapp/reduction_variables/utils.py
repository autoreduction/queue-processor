import logging, os, sys, imp
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, BASE_DIR, REDUCTION_SCRIPT_BASE
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
from django.db import models
from reduction_variables.models import InstrumentVariable
from reduction_viewer.utils import InstrumentUtils

class InstrumentVariablesUtils(object):
    def set_default_instrument_variables(self, instrument_name, start_run):
        reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, instrument_name, 'reduce.py')
        reduce_script = imp.load_source('reduce_script', reduction_file)
        instrument = InstrumentUtils.get_instrument(instrument_name)
        instrument_variables = []
        for key in reduce_script.standard_vars:
            instrument_var = InstrumentVariable(instrument=instrument, name=key, value=reduce_script.standard_vars[key], is_advanced=False, type=type(reduce_script.standard_vars[key]).__name__, start_run=start_run)
            instrument_var.save()
        for key in reduce_script.advanced_vars:
            instrument_var = InstrumentVariable(instrument=instrument, name=key, value=reduce_script.advanced_vars[key], is_advanced=True, type=type(reduce_script.advanced_vars[key]).__name__, start_run=start_run)
            instrument_var.save()