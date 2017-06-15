import logging.config
import re
from settings import LOGGING
from orm_mapping import *
from base import session

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")


class VariableUtils(object):
    @staticmethod
    def derive_run_variable(instrument_var, reduction_run):
        return RunJoin(name=instrument_var.name,
                       value=instrument_var.value,
                       is_advanced=instrument_var.is_advanced,
                       type=instrument_var.type,
                       help_text=instrument_var.help_text,
                       reduction_run=reduction_run,
                       )

    def save_run_variables(self, instrument_vars, reduction_run):
        logger.info('Saving run variables for ' + str(reduction_run.run_number))
        run_variables = map(lambda ins_var: self.derive_run_variable(ins_var, reduction_run), instrument_vars)
        for run_variable in run_variables:
            session.add(run_variable)
        session.commit()
        return run_variables

    @staticmethod
    def copy_variable(variable):
        """
        Return a temporary copy (unsaved) of the variable,
        which can be modified and then saved without modifying the original.
        """
        return InstrumentJoin(name=variable.name,
                              value=variable.value,
                              is_advanced=variable.is_advanced,
                              type=variable.type,
                              help_text=variable.help_text,
                              instrument=variable.instrument,
                              experiment_reference=variable.experiment_reference,
                              start_run=variable.start_run,
                              tracks_script=variable.tracks_script,
                              )

    @staticmethod
    def get_type_string(value):
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

    @staticmethod
    def convert_variable_to_type(value, var_type):
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
