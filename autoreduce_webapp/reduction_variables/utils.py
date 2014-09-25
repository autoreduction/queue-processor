import logging, os, sys, imp, uuid
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, BASE_DIR, REDUCTION_SCRIPT_BASE
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
from django.db import models
from reduction_variables.models import InstrumentVariable, ScriptFile
from reduction_viewer.utils import InstrumentUtils

class InstrumentVariablesUtils(object):
    def set_default_instrument_variables(self, instrument_name, start_run):
        reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, instrument_name, 'reduce.py')
        try:
            reduce_script = imp.load_source('reduce_script', reduction_file)
            f = open(reduction_file, 'rb')
            script_binary = f.read()
        except IOError:
            logging.error("Unable to load reduction script %s" % reduction_file)
            return

        script = ScriptFile(script=script_binary, file_name='reduce.py')
        script.save()

        instrument = InstrumentUtils().get_instrument(instrument_name)
        instrument_variables = []
        for key in reduce_script.standard_vars:
            instrument_var = InstrumentVariable(instrument=instrument, name=key, value=reduce_script.standard_vars[key], is_advanced=False, type=type(reduce_script.standard_vars[key]).__name__, start_run=start_run)
            instrument_var.save()
            instrument_var.scripts.add(script)
            instrument_var.save()
        for key in reduce_script.advanced_vars:
            instrument_var = InstrumentVariable(instrument=instrument, name=key, value=reduce_script.advanced_vars[key], is_advanced=True, type=type(reduce_script.advanced_vars[key]).__name__, start_run=start_run)
            instrument_var.save()
            instrument_var.scripts.add(script)
            instrument_var.save()

class ReductionVariablesUtiles(object):
    def get_script_path_and_arguments(self, run_variables):
        if not run_variables or len(run_variables) == 0:
            raise Exception("Run variables required")
        reduction_run = None
        for variables in run_variables:
            if not reduction_run:
                reduction_run = variables.reduction_run.id
            else:
                if reduction_run is not variables.reduction_run.id:
                    raise Exception("All run variables must be for the same reduction run")

        # Currently only supports a single script file
        script_file = run_variables[0].scripts.all()[0]

        unique_name = uuid.uuid4() + '.py'
        script_path = os.path.join(REDUCTION_SCRIPT_BASE, 'reduction_script_temp', unique_name)
        # Make sure we don't accidently overwrite a file
        while os.path.isfile(script_path):
            unique_name = uuid.uuid4() + '.py'
            script_path = os.path.join(REDUCTION_SCRIPT_BASE, 'reduction_script_temp', unique_name)
        f = open(script_path, 'wb')
        f.write(script_file)
        f.close()

        standard_vars = {}
        advanced_vars = {}
        for variables in run_variables:
            if variables.is_advanced:
                advanced_vars[variables.name] = variables.value
            else:
                standard_vars[variables.name] = variables.value

        arguments = { 'standard_vars' : standard_vars, 'advanced_vars': advanced_vars }

        return (script_path, arguments)

