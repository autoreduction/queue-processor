# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
""" Class to deal with reduction run variables. """
import logging.config
import re

# pylint: disable=import-error,no-name-in-module
from queue_processors.queue_processor.base import session
from queue_processors.queue_processor.orm_mapping import (RunJoin, InstrumentJoin,
                                                          Variable, RunVariable)
# pylint:disable=no-name-in-module,import-error
from queue_processors.queue_processor.settings import LOGGING

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


class VariableUtils:
    """ Class to deal with reduction run variables. """

    @staticmethod
    def find_existing_variable_in_database(variable):
        """
        Find a Variable record in the database and return it's ID
        :param variable: The variable to attempt to find in the database
        :return: The ID if the record exists, else None.
        """
        database_variable = session.query(Variable).filter_by(name=variable.name,
                                                              value=variable.value,
                                                              type=variable.type,
                                                              is_advanced=variable.is_advanced,
                                                              help_text=variable.help_text).first()
        if database_variable:
            return database_variable.id
        return None

    @staticmethod
    def derive_run_variable(instrument_var, reduction_run):
        """
        Create and return a RunJoin record (BOTH variable and RunVariable record)
        :param instrument_var: A variable object to create a database variable object from
        :param reduction_run: The reduction run to join the variable to
        :return: A database object representing the Variable and RunVariable records
        """
        return RunJoin(name=instrument_var.name,
                       value=instrument_var.value,
                       is_advanced=instrument_var.is_advanced,
                       type=instrument_var.type,
                       help_text=instrument_var.help_text,
                       reduction_run=reduction_run)

    @staticmethod
    def construct_run_variable(variable_id, reduction_run_id):
        """
        Create and return ONLY the joining record between the run and the variable
        :param variable_id: The ID of an existing variable within the database
        :param reduction_run_id: The ID of an existing reduction run within the database
        :return: A database object representing the joining record between run and variable
        """
        return RunVariable(variable_ptr_id=variable_id,
                           reduction_run_id=reduction_run_id)

    def save_run_variables(self, instrument_vars, reduction_run):
        """
        For each variable supplied, try to find an existing variable in the database
        If one does exists, add a RunVariable with reference to the existing variable
        Else, create a new Variable and RunVariable linking the variable to the reduction run
        Commit
        """
        logger.info('Saving run variables for %s', str(reduction_run.run_number))
        run_variables = []
        for variable in instrument_vars:
            variable_db_id = self.find_existing_variable_in_database(variable)
            if variable_db_id:
                db_variable = self.construct_run_variable(variable, reduction_run)
            else:
                db_variable = self.derive_run_variable(variable, reduction_run)
            run_variables.append(db_variable)
        self.add_and_commit(run_variables)
        return run_variables

    @staticmethod
    def add_and_commit(db_objects):
        """
        Add and commit the supplied database objects to the database
        This has been refactored to remove the database access layer from the control code
        :param db_objects: A list of database objects created using autoreduction orm_mapping
        """
        for record in db_objects:
            session.add(record)
        session.commit()

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
                              tracks_script=variable.tracks_script)

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
        if var_type in ('int', 'float'):
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
        :param value: A string of the value to convert
        :param var_type: The desired type to convert the value to
        :return: The value as the desired type,
                 or if failed to convert the original value as string
        """
        # pylint: disable=too-many-return-statements,too-many-branches
        if var_type == "text":
            return str(value)
        if var_type == "number":
            if not value or not re.match('(-)?[0-9]+', str(value)):
                return None
            if '.' in str(value):
                return float(value)
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
