import logging, os, sys, imp, uuid, re, json, time, datetime, cgi
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
from autoreduce_webapp.settings import ACTIVEMQ, TEMP_OUTPUT_DIRECTORY, REDUCTION_DIRECTORY, FACILITY
logger = logging.getLogger('django')
from django.utils import timezone
from reduction_variables.models import InstrumentVariable, ScriptFile, RunVariable
from reduction_viewer.models import ReductionRun, Notification, DataLocation
from reduction_viewer.utils import InstrumentUtils, StatusUtils
from autoreduce_webapp.icat_communication import ICATCommunication

class DataTooLong(ValueError):
    pass

def write_script_to_temp(script, script_vars_file):
    """
    Write the given script binary to a unique filename in the reduction_script_temp directory.
    """
    try:
        unique_name = str(uuid.uuid4())
        script_path = os.path.join(TEMP_OUTPUT_DIRECTORY, 'scripts', unique_name)
        # Make sure we don't accidently overwrite a file
        while os.path.exists(script_path):
            unique_name = str(uuid.uuid4())
            script_path = os.path.join(TEMP_OUTPUT_DIRECTORY, 'scripts', unique_name)
        os.makedirs(script_path)
        f = open(os.path.join(script_path, 'reduce.py'), 'wb')
        f.write(script)
        f.close()
        f = open(os.path.join(script_path, 'reduce_vars.py'), 'wb')
        f.write(script_vars_file)
        f.close()
    except Exception as e:
        logger.error("Couldn't write temporary script - %s" % e)
        type, value, traceback = sys.exc_info()
        logger.error('Error opening %s: %s' % (value.filename, value.strerror))
        raise e
    return script_path


def log_error_and_notify(message):
    """
    Helper method to log an error and save a notifcation
    """
    logger.error(message)
    notification = Notification(is_active=True, is_staff_only=True, severity='e', message=message)
    notification.save()


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
    def __load_reduction_script(self, instrument_name):
        """
        Load the relevant reduction script and return back the text of the script
        If the script cannot be loaded None is returned
        """
        reduction_file = os.path.join((REDUCTION_DIRECTORY % (instrument_name)), 'reduce.py')
        try:
            f = open(reduction_file, 'rb')
            script_binary = f.read()
            return script_binary
        except ImportError as e:
            log_error_and_notify("Unable to load reduction script %s due to missing import. (%s)" % (reduction_file, e.message))
            return None
        except IOError:
            log_error_and_notify("Unable to load reduction script %s" % reduction_file)
            return None
        except SyntaxError:
            log_error_and_notify("Syntax error in reduction script %s" % reduction_file)
            return None

    def __load_reduction_vars_script(self, instrument_name):
        """
        Load the relevant reduction script and return back a tuple containing:
            - An instance of the python script
            - The text of the script
        If the script cannot be loaded (None, None) is returned
        """
        reduction_file = os.path.join((REDUCTION_DIRECTORY % (instrument_name)), 'reduce_vars.py')
        try:
            reduce_script = imp.load_source(instrument_name + 'reduce_script', reduction_file)
            f = open(reduction_file, 'rb')
            script_binary = f.read()
            return reduce_script, script_binary
        except ImportError as e:
            log_error_and_notify("Unable to load reduction script %s due to missing import. (%s)" % (reduction_file, e.message))
            return None, None
        except IOError:
            log_error_and_notify("Unable to load reduction script %s" % reduction_file)
            return None, None
        except SyntaxError:
            log_error_and_notify("Syntax error in reduction script %s" % reduction_file)
            return None, None

    def __get_scripts_modified(self, instrument_name):
        """
        Returns the last modification time of the scripts located in the filesystem
        """
        reduction_file = os.path.join((REDUCTION_DIRECTORY % instrument_name), "reduce.py")
        script_mod_time = os.path.getmtime(reduction_file)
        reduction_file = os.path.join((REDUCTION_DIRECTORY % instrument_name), "reduce_vars.py")
        script_vars_mod_time = os.path.getmtime(reduction_file)
        return script_mod_time, script_vars_mod_time

    def __update_variable_scripts(self, variables, script_binary, script_vars_binary):
        """
        Helper method to save a new script into the database and update a set of variables with the script
        """
        script = ScriptFile(script=script_binary, file_name='reduce.py')
        script.save()
        script_vars = ScriptFile(script=script_vars_binary, file_name='reduce_vars.py')
        script_vars.save()

        for variable in variables:
            variable.save()
            variable.scripts.clear()
            variable.scripts.add(script)
            variable.scripts.add(script_vars)
            variable.save()

    def get_variables_from_current_script(self, instrument_name):
        """
        Reloads script in variables to match that on disk. For now ignore modification time check.
        """
        reduce_vars_script, vars_script_binary = self.__load_reduction_vars_script(instrument_name)
        variables = self.get_default_variables(instrument_name, reduce_vars_script)
        script_binary = self.__load_reduction_script(instrument_name)
        self.__update_variable_scripts(variables, script_binary, vars_script_binary)

        return variables

    def set_default_instrument_variables(self, instrument_name, start_run=1):
        """
        Creates and saves a set of variables for the given run number using default values found in the relevant reduce script and returns them.
        If no start_run is supplied, 1 is assumed.
        """
        if not start_run:
            start_run = 1
        script_binary =  self.__load_reduction_script(instrument_name)
        reduce_vars_script, vars_script_binary =  self.__load_reduction_vars_script(instrument_name)

        script = ScriptFile(script=script_binary, file_name='reduce.py')
        script.save()
        script_vars = ScriptFile(script=vars_script_binary, file_name='reduce_vars.py')
        script_vars.save()

        instrument_variables = self.get_default_variables(instrument_name, reduce_vars_script)
        variables = []
        for variable in instrument_variables:
            variable.start_run = start_run
            variable.save()
            variable.scripts.add(script)
            variable.scripts.add(script_vars)
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
        instrument_name = reduction_run.instrument.name
        variables = InstrumentVariable.objects.filter(instrument=reduction_run.instrument, experiment_reference=reduction_run.experiment.reference_number)
        # No experiment-specific variables, lets look for run number
        if not variables:
            try:
                variables_run_start = InstrumentVariable.objects.filter(instrument=reduction_run.instrument,start_run__lte=reduction_run.run_number, experiment_reference__isnull=True ).order_by('-start_run').first().start_run
                variables = InstrumentVariable.objects.filter(instrument=reduction_run.instrument,start_run=variables_run_start)
            except AttributeError:
                # Still not found any variables, we better create some
                variables = self.set_default_instrument_variables(instrument_name)

        if variables[0].tracks_script:
            script_binary = self.__load_reduction_script(instrument_name)
            reduce_vars_script, vars_script_binary = self.__load_reduction_vars_script(instrument_name)
            self.__update_variable_scripts(variables, script_binary, vars_script_binary)

        return variables

    def get_current_script_text(self, instrument_name):
        """
        Returns the binary text within the reduce script for the provided instrument.
        """
        script_binary =  self.__load_reduction_script(instrument_name)
        reduce_vars_script, vars_script_binary =  self.__load_reduction_vars_script(instrument_name)
        return script_binary, vars_script_binary

    def get_temporary_script(self, instrument_name):
        """
        Fetches the reduction script for the given instument, saves it to a temporary location
        and returns the path.
        This is for use when a reduction script doesn't expose any variables
        """
        script_binary, vars_script_binary = self.get_current_script_text(instrument_name)
        return write_script_to_temp(script_binary, vars_script_binary)

    def _create_variables(self, instrument, script, variable_dict, is_advanced):
        variables = []
        for key, value in variable_dict.iteritems():
            str_value = str(value).replace('[','').replace(']','')
            if len(str_value) > InstrumentVariable._meta.get_field('value').max_length:
                raise DataTooLong
            variable = InstrumentVariable(
                instrument=instrument,
                name=key,
                value=str_value,
                is_advanced=is_advanced,
                type=VariableUtils().get_type_string(value),
                start_run = 0,
                help_text=self.get_help_text('standard_vars', key, instrument.name, script),
                )
            variables.append(variable)
        return variables

    def get_default_variables(self, instrument_name, reduce_script=None):
        """
        Creates and returns a list of variables matching those found in the appropriate reduce script.
        An opptional instance of reduce_script can be passed in to prevent multiple hits to the filesystem.
        """
        if not reduce_script:
            reduce_script, script_binary =  self.__load_reduction_vars_script(instrument_name)
        instrument = InstrumentUtils().get_instrument(instrument_name)
        variables = []
        if 'standard_vars' in dir(reduce_script):
            variables.extend(self._create_variables(instrument, reduce_script, reduce_script.standard_vars, False))
        if 'advanced_vars' in dir(reduce_script):
            variables.extend(self._create_variables(instrument, reduce_script, reduce_script.advanced_vars, True))
        return variables

    def _replace_special_chars(self, help_text):
        help_text = cgi.escape(help_text)  # Remove any HTML already in the help string
        help_text = help_text.replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        return help_text

    def get_help_text(self, dictionary, key, instrument_name, reduce_script=None):
        if not dictionary or not key:
            return ""
        if not reduce_script:
            reduce_script, script_binary = self.__load_reduction_vars_script(instrument_name)
        if 'variable_help' in dir(reduce_script):
            if dictionary in reduce_script.variable_help:
                if key in reduce_script.variable_help[dictionary]:
                    return self._replace_special_chars(reduce_script.variable_help[dictionary][key])
        return ""

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
        
        script_binary, script_vars_binary = ScriptUtils().get_reduce_scripts_binary(run_variables[0].scripts.all())

        script_path = write_script_to_temp(script_binary, script_vars_binary)

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
        
                 
    def createRetryRun(self, reductionRun, scripts=None, variables=None, delay=0):
        """
        Create a run ready for re-running based on the run provided. If variables are provided, copy them and associate them with the new one, otherwise generate variables based on the previous run. If ScriptFile objects are supplied, use them, otherwise use the previous run's.
        """
        # find the previous run version, so we don't create a duplicate
        last_version = -1
        for run in ReductionRun.objects.filter(experiment=reductionRun.experiment, run_number=reductionRun.run_number):
            last_version = max(last_version, run.run_version)
            
        try:
            # create the run object and save it
            new_job = ReductionRun(
                instrument = reductionRun.instrument,
                run_number = reductionRun.run_number,
                run_name = "",
                run_version = last_version+1,
                experiment = reductionRun.experiment,
                #started_by=request.user.username, # commented out for the test server only
                status = StatusUtils().get_queued()
                )
            new_job.save()
            
            reductionRun.retry_run = new_job
            reductionRun.retry_when = timezone.now().replace(microsecond=0) + datetime.timedelta(seconds=delay if delay else 0)
            reductionRun.save()
            
            # copy the previous data locations
            for data_location in reductionRun.data_location.all():
                new_data_location = DataLocation(file_path=data_location.file_path, reduction_run=new_job)
                new_data_location.save()
                new_job.data_location.add(new_data_location)
                
            if not variables: # provide variables if they aren't already
                variables = InstrumentVariablesUtils().get_variables_for_run(new_job)
            for var in variables:
                new_var = RunVariable(name=var.name, value=var.value, type=var.type, is_advanced=var.is_advanced, help_text=var.help_text) # copy variable
                new_var.reduction_run = new_job # associate it with the new run
                new_job.run_variables.add(new_var)
                
                # add scripts based on whether some were supplied
                if not scripts:
                    scripts = var.scripts.all()
                for script in scripts:
                    new_var.scripts.add(script)
                    
                new_var.save()
                    
            return new_job
            
        except:
            new_job.delete()
            raise
        


class MessagingUtils(object):
    def send_pending(self, reduction_run, delay=None):
        """
        Sends a message to the queue with the details of the job to run
        """
        from autoreduce_webapp.queue_processor import Client as ActiveMQClient # to prevent circular dependencies

        script_path, arguments = ReductionVariablesUtils().get_script_path_and_arguments(RunVariable.objects.filter(reduction_run=reduction_run))

        data_path = ''
        # Currently only support single location
        data_location = reduction_run.data_location.first()
        if data_location:
            data_path = data_location.file_path
        else:
            raise Exception("No data path found for reduction run")

        message_client = ActiveMQClient(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Webapp_QueueProcessor', True, True)
        message_client.connect()
        data_dict = {
            'run_number':reduction_run.run_number,
            'instrument':reduction_run.instrument.name,
            'rb_number':str(reduction_run.experiment.reference_number),
            'data':data_path,
            'reduction_script':script_path,
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

class ScriptUtils(object):
    def get_reduce_scripts(self, scripts):
        script_out = None
        script_vars_out = None
        for script in scripts:
            if script.file_name == "reduce.py":
                script_out = script
            elif script.file_name == "reduce_vars.py":
                script_vars_out = script
        return script_out, script_vars_out

    def get_reduce_scripts_binary(self, scripts):
        script, script_vars = self.get_reduce_scripts(scripts)
        return script.script, script_vars.script

    def get_cache_scripts_modified(self, scripts):
        """
        Returns the last time the scripts in the database were modified (in seconds since epoch).
        """
        script_modified = None
        script_vars_modified = None

        for script in scripts:
            if script.file_name == "reduce.py":
                script_modified = self._convert_time_from_string(str(script.created))
            elif script.file_name == "reduce_vars.py":
                script_vars_modified = self._convert_time_from_string(str(script.created))
        return script_modified, script_vars_modified

    def _convert_time_from_string(self, string_time):
        time_format = "%Y-%m-%d %H:%M:%S"
        string_time = string_time[:string_time.find('+')]
        return int(time.mktime(time.strptime(string_time, time_format)))