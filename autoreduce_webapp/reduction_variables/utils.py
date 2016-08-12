import logging, os, sys, re, json, cgi, imp
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
from autoreduce_webapp.settings import ACTIVEMQ, REDUCTION_DIRECTORY, FACILITY
logger = logging.getLogger('django')
from reduction_variables.models import InstrumentVariable, RunVariable
from reduction_viewer.models import ReductionRun, Notification
from reduction_viewer.utils import InstrumentUtils, StatusUtils, ReductionRunUtils
from autoreduce_webapp.icat_communication import ICATCommunication

class DataTooLong(ValueError):
    pass


def log_error_and_notify(message):
    """
    Helper method to log an error and save a notifcation
    """
    logger.error(message)
    notification = Notification(is_active=True, is_staff_only=True, severity='e', message=message)
    notification.save()


class VariableUtils(object):
    def derive_run_variable(self, instrument_var, reduction_run):
        return RunVariable( name = instrument_var.name
                          , value = instrument_var.value
                          , is_advanced = instrument_var.is_advanced
                          , type = instrument_var.type
                          , help_text = instrument_var.help_text
                          , reduction_run = reduction_run
                          )
                          
    def save_run_variables(self, instrument_vars, reduction_run):
        runVariables = map(lambda iVar: self.derive_run_variable(iVar, reduction_run), instrument_vars)
        map(lambda rVar: rVar.save(), runVariables)

    def wrap_in_type_syntax(self, value, var_type):
        """
        Append the appropriate syntax around variables to be wrote to a preview script.
        E.g. strings will be wrapped in single quotes, lists will be wrapped in brackets, etc.
        """
        value = str(value)
        if var_type == 'text':
            return "'%s'" % value.replace("'", "\\'")
        if var_type == 'number':
            return re.sub("[^0-9.\-]", "", value)
        if var_type == 'boolean':
            return str(value.lower() == 'true')
        if var_type == 'list_number':
            list_values = value.split(',')
            number_list = []
            for val in list_values:
                if re.match("[\-0-9.]+", val.strip()):
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
            if not value or not re.match('(-)?[0-9]+', str(value)):
                return None
            if '.' in str(value):
                return float(value)
            else:
                return int(re.sub("[^0-9]+", "", str(value)))
        if var_type == "list_text":
            var_list = str(value).split(',')
            list_text = []
            for list_val in var_list:
                if list_val:
                    if list_val and list_val.strip():
                        list_text.append(str(list_val.strip()))
            return list_text
        if var_type == "list_number":
            var_list = value.split(',')
            list_number = []
            for list_val in var_list:
                if list_val:
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
            list_type = "number"
            for val in value:
                if type(val).__name__ == 'str':
                    list_type = "text"
            return "list_" + list_type
        return "text"


class InstrumentVariablesUtils(object):
    def get_default_variables(self, instrument_name, reduce_script=None):
        """
        Creates and returns a list of variables matching those found in the appropriate reduce script.
        An opptional instance of reduce_script can be passed in to prevent multiple hits to the filesystem.
        """
        if not reduce_script:
            reduce_script =  self._load_reduction_vars_script(instrument_name)
            
        reduce_vars_module = imp.new_module("reduce_vars")
        exec reduce_script in reduce_vars_module.__dict__
        
        instrument = InstrumentUtils().get_instrument(instrument_name)
        variables = []
        if 'standard_vars' in dir(reduce_vars_module):
            variables.extend(self._create_variables(instrument, reduce_vars_module, reduce_vars_module.standard_vars, False))
        if 'advanced_vars' in dir(reduce_vars_module):
            variables.extend(self._create_variables(instrument, reduce_vars_module, reduce_vars_module.advanced_vars, True))
        return variables

    def set_default_instrument_variables(self, instrument_name, start_run=1):
        """
        Creates and saves a set of variables for the given run number using default values found in the relevant reduce script and returns them.
        If no start_run is supplied, 1 is assumed.
        """
        if not start_run:
            start_run = 1
            
        reduce_vars_script = self._load_reduction_vars_script(instrument_name)
        instrument_variables = self.get_default_variables(instrument_name, reduce_vars_script)
        
        variables = []
        for variable in instrument_variables:
            variable.start_run = start_run
            variable.save()
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

    def get_variables_for_run(self, reduction_run):
        """
        Fetches the appropriate variables for the given reduction run.
        If instrument variables with a matching experiment reference number is found then these will be used
        otherwise the variables with the closest run start will be used.
        If no variable are found, default variables are created for the instrument and those are returned.
        """
        instrument_name = reduction_run.instrument.name
        variables = InstrumentVariable.objects.filter(instrument=reduction_run.instrument, experiment_reference=reduction_run.experiment.reference_number)
        
        if not variables:
            # No experiment-specific variables, lets look for run number
            try:
                variables_run_start = InstrumentVariable.objects.filter(instrument=reduction_run.instrument,start_run__lte=reduction_run.run_number, experiment_reference__isnull=True ).order_by('-start_run').first().start_run
                variables = InstrumentVariable.objects.filter(instrument=reduction_run.instrument,start_run=variables_run_start)
            except:
                pass
                
        if not variables:
            # Still not found any variables, we better create some
            variables = self.set_default_instrument_variables(instrument_name)
        
        
        # make sure variables are up to date if they need to be
        defaults = self.get_default_variables(instrument_name)
        
        def updateVariable(oldVar, defaultVars):
            matchingVars = filter(lambda var: var.name == oldVar.name, defaultVars)
            try:
                newVar = matchingVars[0]
                map(lambda name: setattr(oldVar, name, getattr(newVar, name)),
                    ["value", "type", "is_advanced", "help_text"])
                oldVar.save()
            except:
                pass
                
        map(lambda var: updateVariable(var, defaults) if var.tracks_script else None, variables)
        return variables
        
    def get_variables_from_current_script(self, instrument_name):
        """
        Reloads script in variables to match that on disk.
        """
        reduce_vars_script = self._load_reduction_vars_script(instrument_name)
        variables = self.get_default_variables(instrument_name, reduce_vars_script)
        return variables

    def get_current_script_text(self, instrument_name):
        """
        Fetches the reduction script and variables script for the given instument, and returns each as a string.
        """
        script_text = self._load_reduction_script(instrument_name)
        script_vars_text = self._load_reduction_vars_script(instrument_name)
        return (script_text, script_vars_text)
        
        
    def _load_script(self, path):
        """
        Load the relevant reduction script and return back the text of the script. If the script cannot be loaded, None is returned.
        """
        try:
            f = open(path, 'r')
            script_text = f.read()
            return script_text
        except Exception as e:
            log_error_and_notify("Unable to load reduction script %s - %s" % (path, e))
            return None
        
    def _load_reduction_script(self, instrument_name):
        return self._load_script(os.path.join(REDUCTION_DIRECTORY % instrument_name, 'reduce.py'))

    def _load_reduction_vars_script(self, instrument_name):
        return self._load_script(os.path.join(REDUCTION_DIRECTORY % instrument_name, 'reduce_vars.py'))
        
    def _create_variables(self, instrument, script, variable_dict, is_advanced):
        variables = []
        for key, value in variable_dict.iteritems():
            str_value = str(value).replace('[','').replace(']','')
            if len(str_value) > InstrumentVariable._meta.get_field('value').max_length:
                raise DataTooLong
            variable = InstrumentVariable( instrument=instrument
                                         , name=key
                                         , value=str_value
                                         , is_advanced=is_advanced
                                         , type=VariableUtils().get_type_string(value)
                                         , start_run = 0
                                         , help_text=self._get_help_text('standard_vars', key, instrument.name, script)
                                         )
            variables.append(variable)
        return variables

    def _get_help_text(self, dictionary, key, instrument_name, reduce_script=None):
        if not dictionary or not key:
            return ""
        if not reduce_script:
            reduce_script = self._load_reduction_vars_script(instrument_name)
        if 'variable_help' in dir(reduce_script):
            if dictionary in reduce_script.variable_help:
                if key in reduce_script.variable_help[dictionary]:
                    return self._replace_special_chars(reduce_script.variable_help[dictionary][key])
        return ""
        
    def _replace_special_chars(self, help_text):
        help_text = cgi.escape(help_text)  # Remove any HTML already in the help string
        help_text = help_text.replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        return help_text

        

class MessagingUtils(object):

    def _make_pending_msg(self, reduction_run):
        """
        Creates a dict message from the given run, ready to be sent to ReductionPending
        """
        script, arguments = ReductionRunUtils().get_script_and_arguments(reduction_run)

        data_path = ''
        # Currently only support single location
        data_location = reduction_run.data_location.first()
        if data_location:
            data_path = data_location.file_path
        else:
            raise Exception("No data path found for reduction run")

        data_dict = {
            'run_number':reduction_run.run_number,
            'instrument':reduction_run.instrument.name,
            'rb_number':str(reduction_run.experiment.reference_number),
            'data':data_path,
            'reduction_script':script,
            'reduction_arguments':arguments,
            'run_version':reduction_run.run_version,
            'facility':FACILITY,
            'message':'',
        }
        
        return data_dict
        
    
    def _send_pending_msg(self, data_dict, delay=None):
        """
        Sends data_dict to ReductionPending (with the specified delay)
        """
        from autoreduce_webapp.queue_processor import Client as ActiveMQClient # to prevent circular dependencies

        message_client = ActiveMQClient(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Webapp_QueueProcessor', False, ACTIVEMQ['SSL'])
        message_client.connect()
        message_client.send('/queue/ReductionPending', json.dumps(data_dict), priority='0', delay=delay)
        message_client.stop()
        

    def send_pending(self, reduction_run, delay=None):
        """
        Sends a message to the queue with the details of the job to run
        """
        data_dict = self._make_pending_msg(reduction_run)
        self._send_pending_msg(data_dict, delay)
        
    def send_cancel(self, reduction_run):
        """
        Sends a message to the queue telling it to cancel any reruns of the job
        """
        data_dict = self._make_pending_msg(reduction_run)
        data_dict["cancel"] = True
        self._send_pending_msg(data_dict)
        
