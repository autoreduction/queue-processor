# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Functions to ensure that the Reduction job is valid before attempting to process the data
"""
from nexusformat.nexus import nxload
from nexusformat.nexus.tree import NeXusError


def is_valid_rb(rb_number):
    """
    Detects if the RB number is valid e.g. (above 0 and not a string)
    :param rb_number:
    :return: An error message if one is generated or None if the RB is valid
    """
    try:
        rb_number = int(rb_number)
        if rb_number > 0:
            return None
        return "Calibration file detected (RB Number less than or equal to 0)"
    except ValueError:
        return "Calibration file detected (RB Number is a string)"


def check_beam_current(run_file_location):
    """
    Ensure that that there is value for beam current in the file else we can assume the beam is off
    :param run_file_location: The location of the run file to inspect
    :return: An error message if one is generated or None if run has beam current
    """
    try:
        nxs_file = nxload(run_file_location, 'r')
        beam_current = nxs_file['raw_data_1/runlog/dae_beam_current/value'].nxdata[0]
        if beam_current >= 0.1:
            return None
        return f"Assuming data is invalid due to beam current value of {beam_current}"
    except NeXusError:
        return f"Unable to read nxs file at location: {run_file_location}"


def validate_job(rb_number, file_location):
    """
    Run all the functions required to validate a single reduction job
    :param rb_number: The RB number to validate
    :param file_location: The location of the run file to validate
    :return: A single error message created from the validation functions OR None if all is ok
    """
    print("***********************CALLING VALIDATE JOB********************")
    ret_vals = list()
    ret_vals.append(is_valid_rb(rb_number))
    ret_vals.append(check_beam_current(file_location))
    errors = [i for i in ret_vals if i]  # Remove all the None types from the list
    validation_error = ' & '.join(errors)
    if validation_error == '':
        return None
    return validation_error
