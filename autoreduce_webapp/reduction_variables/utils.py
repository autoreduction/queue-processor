import logging, os, sys, re, json, cgi, imp, chardet, io
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
from autoreduce_webapp.settings import ACTIVEMQ, REDUCTION_DIRECTORY, FACILITY
logger = logging.getLogger('django')
from reduction_variables.models import InstrumentVariable, RunVariable
from reduction_viewer.models import ReductionRun, Notification
from reduction_viewer.utils import InstrumentUtils, StatusUtils, ReductionRunUtils
from autoreduce_webapp.icat_cache import ICATCache

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
        return runVariables
        
    def copy_variable(self, variable):
        """ Return a temporary copy (unsaved) of the variable, which can be modified and then saved without modifying the original. """
        return InstrumentVariable( name = variable.name
                                 , value = variable.value
                                 , is_advanced = variable.is_advanced
                                 , type = variable.type
                                 , help_text = variable.help_text
                                 , instrument = variable.instrument
                                 , experiment_reference = variable.experiment_reference
                                 , start_run = variable.start_run
                                 , tracks_script = variable.tracks_script
                                 )

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
                item = list_val.strip().strip("'")
                if item:
                    list_text.append(item)
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
    def create_variables_for_run(self, reduction_run):
        """
        Finds the appropriate `InstrumentVariable`s for the given reduction run, and creates `RunVariable`s from them.
        If the run is a re-run, use the previous run's variables.
        If instrument variables set for the run's experiment are found, they're used.
        Otherwise if variables set for the run's run number exist, they'll be used.
        If not, the instrument's default variables will be.
        """
        instrument_name = reduction_run.instrument.name
        variables = []
        
        if not variables:
            # No previous run versions. Find the instrument variables we want to use.
            variables = self.show_variables_for_experiment(instrument_name, reduction_run.experiment.reference_number)

        if not variables:
            # No experiment-specific variables, so let's look for variables set by run number.
            variables = self.show_variables_for_run(instrument_name, reduction_run.run_number)

        if not variables:
            # No variables are set, so we'll use the defaults, and set them them while we're at it.
            variables = self.get_default_variables(instrument_name)
            self.set_variables_for_runs(instrument_name, variables, reduction_run.run_number)

        # Create run variables from these instrument variables, and return them.
        return VariableUtils().save_run_variables(variables, reduction_run)


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
        
        # First, we find the latest run number to determine what's upcoming.
        try:
            latest_completed_run_number = ReductionRun.objects.filter(instrument = instrument, run_version = 0, status = completed_status).order_by('-run_number').first().run_number
        except AttributeError:
            latest_completed_run_number = 1
            
        # Then we find all the upcoming runs and force updating of all subsequent variables.
        upcoming_run_variables = InstrumentVariable.objects.filter(instrument = instrument, start_run__isnull = False, start_run__gt = latest_completed_run_number+1).order_by('start_run')
        upcoming_run_numbers = set([var.start_run for var in upcoming_run_variables])
        [self.show_variables_for_run(instrument_name, run_number) for run_number in upcoming_run_numbers]
        
        # Get the most recent run variables.
        current_variables = self.show_variables_for_run(instrument_name, latest_completed_run_number)
        if not current_variables:
            # If no variables are saved, we'll use the default ones, and set them while we're at it.
            current_variables = self.get_default_variables(instrument_name)
            self.set_variables_for_runs(instrument_name, current_variables)
            
        # And then select the variables for all subsequent run numbers; collect the immediate upcoming variables and all subsequent sets.
        upcoming_variables_by_run = self.show_variables_for_run(instrument_name, latest_completed_run_number+1)
        upcoming_variables_by_run += list(InstrumentVariable.objects.filter(instrument = instrument, start_run__in = upcoming_run_numbers).order_by('start_run'))

        
        # Get the upcoming experiments, and then select all variables for these experiments.
        upcoming_experiments = []
        with ICATCache() as icat:
            upcoming_experiments = list(icat.get_upcoming_experiments_for_instrument(instrument_name))
        upcoming_variables_by_experiment = InstrumentVariable.objects.filter(instrument = instrument, experiment_reference__in = upcoming_experiments).order_by('experiment_reference')
                
        return current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment


    def set_variables_for_experiment(self, instrument_name, variables, experiment_reference):
        """ Given a list of variables, we set them to be the variables used for subsequent runs under the given experiment reference. """
        map(lambda var: var.delete(), self.show_variables_for_experiment(instrument_name, experiment_reference)) # Delete old instrument variables if they exist.
        # Save the new ones.
        for var in variables:
            var.experiment_reference = experiment_reference
            var.save()


    def set_variables_for_runs(self, instrument_name, variables, start_run=0, end_run=None):
        """
        Given a list of variables, we set them to be the variables used for subsequent runs in the given run range.
        If end_run is not supplied, these variables will be ongoing indefinitely.
        If start_run is not supplied, these variables will be set for all run numbers going backwards.
        """
        instrument = InstrumentUtils().get_instrument(instrument_name)

        # In this case we need to make sure that the variables we set will be the only ones used for the range given.
        # If there are variables which apply after the given range ends, we want to create/modify a set to have a start_run after this end_run, with the right values.
        # First, find all variables that are in the range.
        applicable_variables = InstrumentVariable.objects.filter(instrument = instrument, start_run__gte = start_run)
        final_variables = []
        if end_run:
            applicable_variables = applicable_variables.filter(start_run__lte = end_run)
            after_variables = InstrumentVariable.objects.filter(instrument = instrument, start_run = end_run+1).order_by('start_run')
            previous_variables = InstrumentVariable.objects.filter(instrument = instrument, start_run__lt = start_run)
            
            if applicable_variables and not after_variables:
                # The last set of applicable variables extends outside our range.
                final_start = applicable_variables.order_by('-start_run').first().start_run # Find the last set.
                final_variables = list(applicable_variables.filter(start_run = final_start))
                applicable_variables = applicable_variables.exclude(start_run = final_start) # Don't delete the final set.
                
            elif not applicable_variables and not after_variables and previous_variables:
                # There is a previous set that applies but doesn't start or end in the range.
                final_start = previous_variables.order_by('-start_run').first().start_run # Find the last set.
                final_variables = list(previous_variables.filter(start_run = final_start)) # Set them to apply after our variables.
                [VariableUtils().copy_variable(var).save() for var in final_variables] # Also copy them to apply before our variables.
                
            elif not applicable_variables and not after_variables and not previous_variables:
                # There are instrument defaults which apply after our range.
                final_variables = self.get_default_variables(instrument_name)
                
        # Delete all currently saved variables that apply to the range.
        map(lambda var: var.delete(), applicable_variables)
       
        # Modify the range of the final set to after the specified range, if there is one.
        for var in final_variables:
            var.start_run = end_run + 1
            var.save()

        # Then save the new ones.
        for var in variables:
            var.start_run = start_run
            var.save()


    def show_variables_for_experiment(self, instrument_name, experiment_reference):
        """ Look for currently set variables for the experiment. If none are set, return an empty list (or QuerySet) anyway. """
        instrument = InstrumentUtils().get_instrument(instrument_name)
        vars = list(InstrumentVariable.objects.filter(instrument=instrument, experiment_reference=experiment_reference))
        self._update_variables(vars)
        return [VariableUtils().copy_variable(var) for var in vars]


    def show_variables_for_run(self, instrument_name, run_number=None):
        """
        Look for the applicable variables for the given run number. If none are set, return an empty list (or QuerySet) anyway.
        If run_number isn't given, we'll look for variables for the last run number.
        """
        instrument = InstrumentUtils().get_instrument(instrument_name)

        # Find the run number of the latest set of variables that apply to this run; descending order, so the first will be the most recent run number.
        if run_number:
            applicable_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run__lte=run_number).order_by('-start_run')
        else:
            applicable_variables = InstrumentVariable.objects.filter(instrument=instrument).order_by('-start_run')

        if len(applicable_variables) != 0:
            variable_run_number = applicable_variables.first().start_run
            # Select all variables with that run number.
            vars = list(InstrumentVariable.objects.filter(instrument=instrument, start_run=variable_run_number))
            self._update_variables(vars)
            return [VariableUtils().copy_variable(var) for var in vars]
        else:
            return []


    def get_default_variables(self, instrument_name, reduce_script=None):
        """
        Creates and returns a list of variables from the reduction script on disk for the instrument.
        If reduce_script is supplied, return variables using that script instead of the one on disk.
        """
        if not reduce_script:
            reduce_script = self._load_reduction_vars_script(instrument_name)

        reduce_vars_module = self._read_script(reduce_script, os.path.join(self._reduction_script_location(instrument_name), 'reduce_vars.py'))
        if not reduce_vars_module:
            return []

        instrument = InstrumentUtils().get_instrument(instrument_name)
        variables = []
        if 'standard_vars' in dir(reduce_vars_module):
            variables.extend(self._create_variables(instrument, reduce_vars_module, reduce_vars_module.standard_vars, False))
        if 'advanced_vars' in dir(reduce_vars_module):
            variables.extend(self._create_variables(instrument, reduce_vars_module, reduce_vars_module.advanced_vars, True))
            
        for var in variables:
            var.tracks_script = True
            
        return variables


    def get_current_script_text(self, instrument_name):
        """
        Fetches the reduction script and variables script for the given instrument, and returns each as a string.
        """
        script_text = self._load_reduction_script(instrument_name)
        script_vars_text = self._load_reduction_vars_script(instrument_name)
        return (script_text, script_vars_text)
        
        
    def _update_variables(self, variables, save=True):
        """ 
        Updates all variables with tracks_script to their value in the script, and append any new ones. 
        This assumes that the variables all belong to the same instrument, and that the list supplied is complete.
        If no variables have tracks_script set, we won't do anything at all.
        variables should be a list; it needs to be mutable so that this function can add/remove variables.
        If the 'save' option is true, it will save/delete the variables from the database as required.
        """
        if not any([hasattr(var, "tracks_script") and var.tracks_script for var in variables]):
            return       
        
        # New variable set from the script
        defaults = self.get_default_variables(variables[0].instrument.name) if variables else []
        
        # Update the existing variables
        def updateVariable(oldVar):
            oldVar.keep = True
            matchingVars = filter(lambda var: var.name == oldVar.name, defaults) # Find the new variable from the script.
            if matchingVars and oldVar.tracks_script: # Check whether we should and can update the old one.
                newVar = matchingVars[0]
                map(lambda name: setattr(oldVar, name, getattr(newVar, name)),
                    ["value", "type", "is_advanced", "help_text"]) # Copy the new one's important attributes onto the old variable.
                if save: oldVar.save()
            elif not matchingVars:
                # Or remove the variable if it doesn't exist any more.
                if save: oldVar.delete()
                oldVar.keep = False
        map(updateVariable, variables)
        variables[:] = [var for var in variables if var.keep]
        
        # Add any new ones
        current_names = [var.name for var in variables]
        new_vars = [var for var in defaults if var.name not in current_names]
        def copyMetadata(newVar):
            sourceVar = variables[0]
            if isinstance(sourceVar, InstrumentVariable):
                # Copy the source variable's metadata to the new one.
                map(lambda name: setattr(newVar, name, getattr(sourceVar, name)), ["instrument", "experiment_reference", "start_run"])
            elif isinstance(sourceVar, RunVariable):
                # Create a run variable.
                VariableUtils().derive_run_variable(newVar, sourceVar.reduction_run)
            else: return
            newVar.save()
        map(copyMetadata, new_vars)
        variables += list(new_vars)
        

    def _read_script(self, script_text, script_path):
        """ Takes a python script as a text string, and returns it loaded as a module. Failure will return None, and notify. """
        if not script_text or not script_path:
            return None

        module_name = os.path.basename(script_path).split(".")[0] # file name without extension
        script_module = imp.new_module(module_name)
        try:
            exec script_text in script_module.__dict__
            return script_module
        except ImportError as e:
            log_error_and_notify("Unable to load reduction script %s due to missing import. (%s)" % (script_path, e.message))
            return None
        except SyntaxError:
            log_error_and_notify("Syntax error in reduction script %s" % script_path)
            return None

        
    def _load_script(self, path):
        """
        First detect the file encoding using chardet.
        Then load the relevant reduction script and return back the text of the script.
        If the script cannot be loaded, None is returned.
        """
        try:
            # Read raw bytes and determine encoding
            f_raw = io.open(path, 'rb')
            encoding = chardet.detect(f_raw.read(32))["encoding"]
            
            # Read the file in decoded; io is used for the encoding kwarg
            f = io.open(path, 'r', encoding=encoding)
            script_text = f.read()
            return script_text
        except Exception as e:
            log_error_and_notify("Unable to load reduction script %s - %s" % (path, e))
            return None

    def _reduction_script_location(self, instrument_name):
        return REDUCTION_DIRECTORY % instrument_name

    def _load_reduction_script(self, instrument_name):
        return self._load_script(os.path.join(self._reduction_script_location(instrument_name), 'reduce.py'))

    def _load_reduction_vars_script(self, instrument_name):
        return self._load_script(os.path.join(self._reduction_script_location(instrument_name), 'reduce_vars.py'))

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
    def send_pending(self, reduction_run, delay=None):
        """ Sends a message to the queue with the details of the job to run. """
        data_dict = self._make_pending_msg(reduction_run)
        self._send_pending_msg(data_dict, delay)

    def send_cancel(self, reduction_run):
        """ Sends a message to the queue telling it to cancel any reruns of the job. """
        data_dict = self._make_pending_msg(reduction_run)
        data_dict["cancel"] = True
        self._send_pending_msg(data_dict)

    def _make_pending_msg(self, reduction_run):
        """ Creates a dict message from the given run, ready to be sent to ReductionPending. """
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
        """ Sends data_dict to ReductionPending (with the specified delay) """
        from autoreduce_webapp.queue_processor import Client as ActiveMQClient # to prevent circular dependencies

        message_client = ActiveMQClient(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Webapp_QueueProcessor', False, ACTIVEMQ['SSL'])
        message_client.connect()
        message_client.send('/queue/ReductionPending', json.dumps(data_dict), priority='0', delay=delay)
        message_client.stop()
