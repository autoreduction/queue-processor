import os
import io
import logging.config
import chardet
import imp
import cgi
from settings import REDUCTION_DIRECTORY, LOGGING
from orm_mapping import *
from variable_utils import VariableUtils
from instrument_utils import InstrumentUtils
from base import session

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")


class DataTooLong(ValueError):
    pass


class InstrumentVariablesUtils(object):
    @staticmethod
    def log_error_and_notify(message):
        """
        Helper method to log an error and save a notifcation
        """
        logger.error(message)
        notification = Notification(is_active=True, is_staff_only=True, severity='e', message=message)
        session.add(notification)
        session.commit()

    def show_variables_for_run(self, instrument_name, run_number=None):
        """
        Look for the applicable variables for the given run number. If none are set, return an empty list (or QuerySet)
        anyway.
        """
        instrument = InstrumentUtils().get_instrument(instrument_name)
        variable_run_number = 0

        # If we haven't been given a run number, we should try to find it.
        if not run_number:
            applicable_variables = session.query(InstrumentVariable).filter_by(instrument=instrument) \
                .order_by('-start_run').all()
            if len(applicable_variables) != 0:
                variable_run_number = applicable_variables[0].start_run
        else:
            variable_run_number = run_number

        # Now use the InstrumentJoin class (which is a join of the InstrumentVariable and Variable tables) to make sure
        # we can make a copy of all the relevant variables with all of the right information.
        variables = (session.query(InstrumentJoin).filter_by(instrument=instrument,
                                                             start_run=variable_run_number)).all()

        # If we have found some variables then we want to use them by first making copies of them and sending them back
        # to be used. This means we don't alter the previous set of variables. If we haven't found any variables, just
        # return an empty list.
        if len(variables) != 0:
            self._update_variables(variables)
            new_variables = []
            for variable in variables:
                new_variables.append(VariableUtils().copy_variable(variable))
            return new_variables
        else:
            return []

    def get_default_variables(self, instrument_name, reduce_script=None):
        """
        Creates and returns a list of variables from the reduction script on disk for the instrument.
        If reduce_script is supplied, return variables using that script instead of the one on disk.
        """
        if not reduce_script:
            reduce_script = self._load_reduction_vars_script(instrument_name)

        reduce_vars_module = self._read_script(reduce_script,
                                               os.path.join(self._reduction_script_location(instrument_name),
                                                            'reduce_vars.py'))
        if not reduce_vars_module:
            return []

        instrument = InstrumentUtils().get_instrument(instrument_name)
        variables = []
        if 'standard_vars' in dir(reduce_vars_module):
            variables.extend(
                self._create_variables(instrument, reduce_vars_module, reduce_vars_module.standard_vars, False))
        if 'advanced_vars' in dir(reduce_vars_module):
            variables.extend(
                self._create_variables(instrument, reduce_vars_module, reduce_vars_module.advanced_vars, True))

        for var in variables:
            var.tracks_script = True

        applicable_variables = session.query(InstrumentVariable).filter_by(instrument=instrument) \
            .order_by('-start_run').all()
        variable_run_number = applicable_variables[0].start_run

        # Now use the InstrumentJoin class (which is a join of the InstrumentVariable and Variable tables) to make sure
        # we can make a copy of all the relevant variables with all of the right information.
        variables = (session.query(InstrumentJoin).filter_by(instrument=instrument,
                                                             start_run=variable_run_number)).all()

        return variables

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
        def update_variable(old_var):
            old_var.keep = True
            # Find the new variable from the script.
            matching_vars = filter(lambda temp_var: temp_var.name == old_var.name, defaults)
            if matching_vars and old_var.tracks_script:  # Check whether we should and can update the old one.
                new_var = matching_vars[0]
                map(lambda name: setattr(old_var, name, getattr(new_var, name)),
                    ["value", "type", "is_advanced",
                     "help_text"])  # Copy the new one's important attributes onto the old variable.
                if save:
                    session.add(old_var)
                    session.commit()
            elif not matching_vars:
                # Or remove the variable if it doesn't exist any more.
                if save:
                    session.delete(old_var)
                    session.commit()
                old_var.keep = False

        map(update_variable, variables)
        variables[:] = [var for var in variables if var.keep]

        # Add any new ones
        current_names = [var.name for var in variables]
        new_vars = [var for var in defaults if var.name not in current_names]

        def copy_metadata(new_var):
            source_var = variables[0]
            if isinstance(source_var, InstrumentVariable):
                # Copy the source variable's metadata to the new one.
                map(lambda name: setattr(new_var, name, getattr(source_var, name)),
                    ["instrument", "experiment_reference", "start_run"])
            elif isinstance(source_var, RunVariable):
                # Create a run variable.
                VariableUtils().derive_run_variable(new_var, source_var.reduction_run)
            else:
                return
            session.add(new_var)
            session.commit()

        map(copy_metadata, new_vars)
        variables += list(new_vars)

    @staticmethod
    def _reduction_script_location(instrument_name):
        return REDUCTION_DIRECTORY % instrument_name

    def _load_reduction_script(self, instrument_name):
        return self._load_script(os.path.join(self._reduction_script_location(instrument_name), 'reduce.py'))

    def _load_reduction_vars_script(self, instrument_name):
        return self._load_script(os.path.join(self._reduction_script_location(instrument_name), 'reduce_vars.py'))

    def _read_script(self, script_text, script_path):
        """
        Takes a python script as a text string, and returns it loaded as a module.
        Failure will return None, and notify.
        """
        if not script_text or not script_path:
            return None

        module_name = os.path.basename(script_path).split(".")[0]  # file name without extension
        script_module = imp.new_module(module_name)
        try:
            exec script_text in script_module.__dict__
            return script_module
        except ImportError as e:
            self.log_error_and_notify(
                "Unable to load reduction script %s due to missing import. (%s)" % (script_path, e.message))
            return None
        except SyntaxError:
            self.log_error_and_notify("Syntax error in reduction script %s" % script_path)
            return None

    def _create_variables(self, instrument, script, variable_dict, is_advanced):
        variables = []
        for key, value in variable_dict.iteritems():
            str_value = str(value).replace('[', '').replace(']', '')
            if len(str_value) > 300:
                raise DataTooLong

            variable = Variable(name=key,
                                value=str_value,
                                type=VariableUtils().get_type_string(value),
                                is_advanced=is_advanced,
                                help_text=self._get_help_text('standard_vars', key, instrument.name, script)
                                )

            instrument_variable = InstrumentVariable(start_run=0,
                                                     instrument=instrument,
                                                     variable=variable,
                                                     tracks_script=1
                                                     )

            session.add(variable)
            session.add(instrument_variable)
            session.commit()

            variables.append(instrument_variable)
        return variables

    def get_current_script_text(self, instrument_name):
        """
        Fetches the reduction script and variables script for the given
        instrument, and returns each as a string.
        """
        script_text = self._load_reduction_script(instrument_name)
        script_vars_text = self._load_reduction_vars_script(instrument_name)
        return script_text, script_vars_text

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
            self.log_error_and_notify("Unable to load reduction script %s - %s" % (path, e))
            return None

    def create_variables_for_run(self, reduction_run):
        """
        Finds the appropriate InstrumentVariables for the given reduction run, and creates RunVariables from them.
        If the run is a re-run, use the previous run's variables.
        If instrument variables set for the run's experiment are found, they're used.
        Otherwise if variables set for the run's run number exist, they'll be used.
        If not, the instrument's default variables will be used.
        """
        instrument_name = reduction_run.instrument.name

        variables = []

        if not variables:
            logger.info('Finding variables from experiment')
            # No previous run versions. Find the instrument variables we want to use.
            variables = self.show_variables_for_experiment(instrument_name, reduction_run.experiment.reference_number)

        if not variables:
            logger.info('Finding variables from run number')
            # No experiment-specific variables, so let's look for variables set by run number.
            variables = self.show_variables_for_run(instrument_name, reduction_run.run_number)

        if not variables:
            logger.info('Using default variables')
            # No variables are set, so we'll use the defaults, and set them them while we're at it.
            variables = self.get_default_variables(instrument_name)
            logger.info('Setting the variables for the run')
            self.set_variables_for_runs(instrument_name, variables, reduction_run.run_number)

        logger.info('Saving the found variables')
        # Create run variables from these instrument variables, and return them.
        return VariableUtils().save_run_variables(variables, reduction_run)

    def set_variables_for_runs(self, instrument_name, variables, start_run=0, end_run=None):
        """
        Given a list of variables, we set them to be the variables used for subsequent runs in the given run range.
        If end_run is not supplied, these variables will be ongoing indefinitely.
        If start_run is not supplied, these variables will be set for all run numbers going backwards.
        """
        instrument = InstrumentUtils().get_instrument(instrument_name)
        """
        In this case we need to make sure that the variables we set will be the only ones used for the range given.
        If there are variables which apply after the given range ends, we want to create/modify a set to have a
        start_run after this end_run, with the right values. First, find all variables that are in the range.
        """
        applicable_variables = session.query(InstrumentVariable).filter_by(instrument=instrument,
                                                                           start_run=start_run).all()
        final_variables = []
        if end_run:
            applicable_variables = applicable_variables.filter(start_run__lte=end_run)
            after_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run=end_run + 1).order_by(
                'start_run')
            previous_variables = InstrumentVariable.objects.filter(instrument=instrument, start_run__lt=start_run)

            if applicable_variables and not after_variables:
                # The last set of applicable variables extends outside our range.
                final_start = applicable_variables.order_by('-start_run').first().start_run  # Find the last set.
                final_variables = list(applicable_variables.filter(start_run=final_start))
                applicable_variables = applicable_variables.exclude(
                    start_run=final_start)  # Don't delete the final set.

            elif not applicable_variables and not after_variables and previous_variables:
                # There is a previous set that applies but doesn't start or end in the range.
                final_start = previous_variables.order_by('-start_run').first().start_run  # Find the last set.
                final_variables = list(
                    previous_variables.filter(start_run=final_start))  # Set them to apply after our variables.
                [VariableUtils().copy_variable(var).save() for var in
                 final_variables]  # Also copy them to apply before our variables.

            elif not applicable_variables and not after_variables and not previous_variables:
                # There are instrument defaults which apply after our range.
                final_variables = self.get_default_variables(instrument_name)

        # Delete all currently saved variables that apply to the range.
        map(lambda temp_var: temp_var.delete(), applicable_variables)

        # Modify the range of the final set to after the specified range, if there is one.
        for var in final_variables:
            var.start_run = end_run + 1
            session.add(var)
            session.commit()

        # Then save the new ones.
        for var in variables:
            var.start_run = start_run
            session.add(var)
            session.commit()

    def show_variables_for_experiment(self, instrument_name, experiment_reference):
        """
        Look for currently set variables for the experiment.
        If none are set, return an empty list (or QuerySet) anyway.
        """
        instrument = InstrumentUtils().get_instrument(instrument_name)
        ins_vars = session.query(InstrumentVariable).filter_by(instrument=instrument,
                                                               experiment_reference=experiment_reference).all()
        self._update_variables(ins_vars)
        return [VariableUtils().copy_variable(ins_var) for ins_var in ins_vars]

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

    @staticmethod
    def _replace_special_chars(help_text):
        help_text = cgi.escape(help_text)  # Remove any HTML already in the help string
        help_text = help_text.replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        return help_text
