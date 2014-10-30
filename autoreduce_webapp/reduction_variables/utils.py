import logging, os, sys, imp, uuid, re, json
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, BASE_DIR, REDUCTION_SCRIPT_BASE, ACTIVEMQ
from autoreduce_webapp.queue_processor import Client as ActiveMQClient
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
from django.db import models
from reduction_variables.models import InstrumentVariable, ScriptFile, RunVariable
from reduction_viewer.models import Instrument
from reduction_viewer.utils import InstrumentUtils

class VariableUtils(object):
    def wrap_in_type_syntax(self, value, var_type):
        if var_type == 'text':
            return "'%s'" % value.replace("'", "\\'")
        if var_type == 'number':
            return re.sub("[^0-9.]", "", value)
        if var_type == 'boolean':
            return value.lower() == 'true'
        if var_type == 'list_number':
            return '[%s]' % value
        if var_type == 'list_text':
            list_values = value.split(',')
            for val in list_values:
                val = "'%s'" % val.strip().replace("'", "\\'")
            return '[%s]' % ','.join(list_values)

    def convert_variable_to_type(self, value, var_type):
        if var_type == "text":
            return str(value)
        if var_type == "number":
            if '.' in value:
                return float(value)
            else:
                return int(value)
        if var_type == "list_text":
            var_list = value.split(',')
            for list_val in var_list:
                list_val = str(list_val)
            return var_list
        if var_type == "list_number":
            var_list = value.split(',')
            for list_val in var_list:
                if '.' in value:
                    list_val = float(list_val)
                else:
                    list_val = int(list_val)
            return var_list
        if var_type == "bool":
            return value.lower() == 'true'

    def get_type_string(self, value):
        var_type = type(value).__name__
        if var_type == 'str':
            return "text"
        if var_type == 'int' or var_type == 'float':
            return "number"
        if var_type == 'bool':
            return "boolean"
        if var_type == 'list':
            if len(value) == 0 or type(value[0]).__name__ == 'str':
                return "list_text"
            if type(value[0]).__name__ == 'int' or type(value[0]).__name__ == 'float':
                return "list_number"
        return "text"

class InstrumentVariablesUtils(object):
    def __load_reduction_script(self, instrument_name):
        reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, instrument_name, 'reduce.py')
        try:
            reduce_script = imp.load_source('reduce_script', reduction_file)
            f = open(reduction_file, 'rb')
            script_binary = f.read()
            return reduce_script, script_binary
        except IOError:
            logging.error("Unable to load reduction script %s" % reduction_file)
            return None, None

    def set_default_instrument_variables(self, instrument_name, start_run):
        if not start_run:
            start_run = 1
        reduce_script, script_binary =  self.__load_reduction_script(instrument_name)

        script = ScriptFile(script=script_binary, file_name='reduce.py')
        script.save()

        instrument_variables = self.get_default_variables(instrument_name)
        for variable in instrument_variables:
            variable.start_run = start_run
            variable.save()
            variable.scripts.add(script)
            variable.save()

    def get_variables_for_run(self, instrument_name, run_number):
        instrument = Instrument.objects.get(name=instrument_name)
        variables_run_start = InstrumentVariable.objects.filter(instrument=instrument,start_run__lte=run_number ).order_by('-start_run').first().start_run
        return InstrumentVariable.objects.filter(instrument=instrument,start_run=variables_run_start )

    def get_current_script(self, instrument_name):
        reduce_script, script_binary =  self.__load_reduction_script(instrument_name)
        return script_binary

    def get_default_variables(self, instrument_name):
        reduce_script, script_binary =  self.__load_reduction_script(instrument_name)
        instrument = InstrumentUtils().get_instrument(instrument_name)
        variables = []
        for key in reduce_script.standard_vars:
            variable = InstrumentVariable(
                instrument=instrument, 
                name=key, 
                value=str(reduce_script.standard_vars[key]).replace('[','').replace(']',''), 
                is_advanced=False, 
                type=VariableUtils().get_type_string(reduce_script.standard_vars[key]),
                start_run = 0,
                )
            variables.append(variable)
        for key in reduce_script.advanced_vars:
            variable = InstrumentVariable(
                instrument=instrument, 
                name=key, 
                value=str(reduce_script.advanced_vars[key]).replace('[','').replace(']',''), 
                is_advanced=True, 
                type=VariableUtils().get_type_string(reduce_script.advanced_vars[key]),
                start_run = 0,
                )
            variables.append(variable)
        return variables

class ReductionVariablesUtils(object):
    def get_script_path_and_arguments(self, run_variables):
        if not run_variables or len(run_variables) == 0:
            raise Exception("Run variables required")
        reduction_run = None
        for variables in run_variables:
            if variables.scripts is None or len(variables.scripts.all()) == 0:
                raise Exception("Run variables missing scripts")
            if not reduction_run:
                reduction_run = variables.reduction_run.id
            else:
                if reduction_run is not variables.reduction_run.id:
                    raise Exception("All run variables must be for the same reduction run")

        # Currently only supports a single script file
        script_file = run_variables[0].scripts.all()[0]

        unique_name = str(uuid.uuid4()) + '.py'
        script_path = os.path.join(REDUCTION_SCRIPT_BASE, 'reduction_script_temp', unique_name)
        # Make sure we don't accidently overwrite a file
        while os.path.isfile(script_path):
            unique_name = str(uuid.uuid4()) + '.py'
            script_path = os.path.join(REDUCTION_SCRIPT_BASE, 'reduction_script_temp', unique_name)
        f = open(script_path, 'wb')
        f.write(script_file.script)
        f.close()

        standard_vars = {}
        advanced_vars = {}
        for variables in run_variables:
            value = VariableUtils().convert_variable_to_type(variables.value, variables.type)
            if variables.is_advanced:
                advanced_vars[variables.name] = value
            else:
                standard_vars[variables.name] = value

        arguments = { 'standard_vars' : standard_vars, 'advanced_vars': advanced_vars }

        return (script_path, arguments)

class MessagingUtils(object):
    def send_pending(self, reduction_run):
        script_path, arguments = ReductionVariablesUtils().get_script_path_and_arguments(RunVariable.objects.filter(reduction_run=reduction_run))

        # Currently only support single location
        data_path = reduction_run.data_location.first()

        message_client = ActiveMQClient(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Webapp_QueueProcessor', True)
        message_client.connect()
        data_dict = {
            'run_number':reduction_run.run_number,
            'instrument':reduction_run.instrument.name,
            'rb_number':reduction_run.experiment.reference_number,
            'data':'',
            'reduction_script':script_path,
            'reduction_arguments':arguments,
            'run_version':reduction_run.run_version,
            'message':'',
        }
        message_client.send('/queue/ReductionPending', json.dumps(data_dict))    
