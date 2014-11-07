import logging, os, sys, imp, uuid, re, json
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, BASE_DIR, REDUCTION_SCRIPT_BASE, ACTIVEMQ
from autoreduce_webapp.queue_processor import Client as ActiveMQClient
logging.basicConfig(filename=LOG_FILE,level=LOG_LEVEL)
from django.db import models
from reduction_variables.models import InstrumentVariable, ScriptFile, RunVariable
from reduction_viewer.models import ReductionRun, Instrument, Notification
from reduction_viewer.utils import InstrumentUtils, StatusUtils
from autoreduce_webapp.icat_communication import ICATCommunication

class VariableUtils(object):
    def wrap_in_type_syntax(self, value, var_type):
        """
        Append the appropriate syntax around variables to be wrote to a preview script.
        E.g. strings will be wrapped in single quotes, lists will be wrapped in brackets, etc.
        """
        value = str(value)
        if var_type == 'text':
            return "'%s'" % value.replace("'", "\\'")
        if var_type == 'number':
            return re.sub("[^0-9.]", "", value)
        if var_type == 'boolean':
            return str(value.lower() == 'true')
        if var_type == 'list_number':
            list_values = value.split(',')
            number_list = []
            for val in list_values:
                if re.match("[0-9.]+", val.strip()):
                    number_list.append(val)
            return '[%s]' % ','.join(number_list)
        if var_type == 'list_text':
            list_values = value.split(',')
            text_list = []
            for val in list_values:
                if val:
                    val = "'%s'" % val.strip().replace("'", "\\'")
                    text_list.append(val)
            return '[%s]' % ','.join(text_list)
        return value

    def convert_variable_to_type(self, value, var_type):
        """
        Convert the given value a type matching that of var_type.
        Options for var_type: text, number, list_text, list_number, boolean
        If the var_type isn't recognised, the value is returned unchanged
        """
        if var_type == "text":
            return str(value)
        if var_type == "number":
            if '.' in str(value):
                return float(value)
            else:
                return int(re.sub("[^0-9]+", "", str(value)))
        if var_type == "list_text":
            var_list = str(value).split(',')
            list_text = []
            for list_val in var_list:
                if list_val and list_val.strip():
                    list_text.append(str(list_val.strip()))
            return list_text
        if var_type == "list_number":
            var_list = value.split(',')
            list_number = []
            for list_val in var_list:
                if '.' in str(list_val):
                    list_number.append(float(list_val))
                else:
                    list_number.append(int(list_val))
            return list_number
        if var_type == "boolean":
            return value.lower() == 'true'
        return value

    def get_type_string(self, value):
        """
        Returns a textual representation of the type of the given value.
        The possible returned types are: text, number, list_text, list_number, boolean
        If the type isn't supported, it defaults to text.
        """
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
        """
        Load the relevant reduction script and return back a tuple containing:
            - An instance of the python script
            - The text of the script
        If the script cannot be loaded (None, None) is returned
        """
        reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, instrument_name, 'reduce.py')
        try:
            reduce_script = imp.load_source(instrument_name + 'reduce_script', reduction_file)
            f = open(reduction_file, 'rb')
            script_binary = f.read()
            return reduce_script, script_binary
        except IOError:
            logging.error("Unable to load reduction script %s" % reduction_file)
            notification = Notification(is_active=True, is_staff_only=True,severity='e', message="Unable to open reduction script for %s" % instrument_name)
            notification.save()
            return None, None
        except SyntaxError:
            logging.error("Syntax error in reduction script %s" % reduction_file)
            notification = Notification(is_active=True, is_staff_only=True,severity='e', message="Syntax error in reduction script for %s" % instrument_name)
            notification.save()
            return None, None

    def set_default_instrument_variables(self, instrument_name, start_run=1):
        """
        Creates and saves a set of variables for the given run number using default values found in the relevant reduce script and returns them.
        If no start_run is supplied, 1 is assumed.
        """
        if not start_run:
            start_run = 1
        reduce_script, script_binary =  self.__load_reduction_script(instrument_name)

        script = ScriptFile(script=script_binary, file_name='reduce.py')
        script.save()

        instrument_variables = self.get_default_variables(instrument_name, reduce_script)
        variables = []
        for variable in instrument_variables:
            variable.start_run = start_run
            variable.save()
            variable.scripts.add(script)
            variable.save()
            variables.append(variable)

        return variables

    def get_variables_for_run(self, reduction_run):
        """
        Fetches the appropriate variables for the given reduction run.
        If instrument variables with a matching experiment reference number is found then these will be used
        otherwise the variables with the closest run start will be used.
        If no variable are found, default variables are created for the instrument and those are returned.
        """
        variables = InstrumentVariable.objects.filter(instrument=reduction_run.instrument, experiment_reference=reduction_run.experiment.reference_number)
        # No experiment-specific variables, lets look for run number
        if not variables:
            try:
                variables_run_start = InstrumentVariable.objects.filter(instrument=reduction_run.instrument,start_run__lte=reduction_run.run_number, experiment_reference__isnull=True ).order_by('-start_run').first().start_run
                variables = InstrumentVariable.objects.filter(instrument=reduction_run.instrument,start_run=variables_run_start)
            except AttributeError:
                # Still not found any variables, we better create some
                variables = self.set_default_instrument_variables(reduction_run.instrument.name)
        return variables

    def get_current_script_text(self, instrument_name):
        """
        Returns the binary text within the reduce script for the provided instrument.
        """
        reduce_script, script_binary =  self.__load_reduction_script(instrument_name)
        return script_binary

    def get_default_variables(self, instrument_name, reduce_script=None):
        """
        Creates and returns a list of variables matching those found in the appropriate reduce script.
        An opptional instance of reduce_script can be passed in to prevent multiple hits to the filesystem.
        """
        if not reduce_script:
            reduce_script, script_binary =  self.__load_reduction_script(instrument_name)
        instrument = InstrumentUtils().get_instrument(instrument_name)
        variables = []
        if 'standard_vars' in dir(reduce_script):
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
        if 'advanced_vars' in dir(reduce_script):
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

    def get_current_and_upcoming_variables(self, instrument_name):
        """
        Fetches the instrument variables for:
        - The next run number
        - Upcoming run numbers
        - Upcoming known experiments
        as a tuple of (current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment)
        """
        instrument = InstrumentUtils().get_instrument(instrument_name)
        completed_status = StatusUtils().get_completed()

        # Get latest run number and latest experiment reference
        try:
            latest_completed_run = ReductionRun.objects.filter(instrument=instrument, run_version=0, status=completed_status).order_by('-run_number').first()
            latest_completed_run_number = latest_completed_run.run_number
        except AttributeError :
            latest_completed_run_number = 1

        # Get the run number of the closest instrument variables
        try:
            current_variables_run_start = InstrumentVariable.objects.filter(instrument=instrument,start_run__lte=latest_completed_run_number).order_by('-start_run').first().start_run
        except AttributeError :
            current_variables_run_start = 1

        current_variables = InstrumentVariable.objects.filter(instrument=instrument,start_run=current_variables_run_start)
        upcoming_variables_by_run = InstrumentVariable.objects.filter(instrument=instrument, start_run__isnull=False,start_run__gt=latest_completed_run_number ).order_by('start_run')

        upcoming_experiments = []
        with ICATCommunication() as icat:
            upcoming_experiments = list(icat.get_upcoming_experiments_for_instrument(instrument_name))

        upcoming_variables_by_experiment = InstrumentVariable.objects.filter(instrument=instrument,experiment_reference__in=upcoming_experiments).order_by('experiment_reference')

        # If no variables are saved, use the dfault ones from the reduce script
        if not current_variables:
            self.set_default_instrument_variables(instrument.name, current_variables_run_start)
            current_variables = InstrumentVariable.objects.filter(instrument=instrument,start_run=current_variables_run_start )

        return current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment

class ReductionVariablesUtils(object):
    def get_script_path_and_arguments(self, run_variables):
        """
        Fetches the reduction script from the given variables, saves it to a temporary location 
        and returns the path with a dictionary of arguments
        """
        if not run_variables or len(run_variables) == 0:
            raise Exception("Run variables required")
        reduction_run = None
        for variables in run_variables:
            if variables.scripts is None or len(variables.scripts.all()) == 0:
                raise Exception("Run variables missing scripts")
            if not reduction_run:
                reduction_run = variables.reduction_run.id
            else:
                if reduction_run != variables.reduction_run.id:
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
        """
        Sends a message to the queue with the details of the job to run
        """
        script_path, arguments = ReductionVariablesUtils().get_script_path_and_arguments(RunVariable.objects.filter(reduction_run=reduction_run))

        # Currently only support single location
        data_path = reduction_run.data_location.first()

        message_client = ActiveMQClient(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Webapp_QueueProcessor', True, True)
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
