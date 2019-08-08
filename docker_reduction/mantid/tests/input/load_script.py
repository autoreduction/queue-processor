# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Used to test that a file can be loaded into mantid from the input directory and
output to the output directory
"""
import numpy  # Required due to Mantid4.0 import issue
import os
import sys

# Ensure that Mantid does not attempt to plot to display
os.environ['MPLBACKEND'] = 'Agg'

sys.path.append("/isis/NDXENGINX/user/scripts/autoreduction")
sys.path.append("/opt/Mantid/scripts")  # Temporary solution until next Mantid release
import reduce_vars as web_var
import Engineering.EnginX as Enginx

# Require early load import to check for event file
from mantid.simpleapi import Load

import time


def validate(input_file, output_dir):
    """
    Autoreduction validate Function
    -------------------------------

    Function to ensure that the files we want to use in reduction exist.
    Please add any files/directories to the required_files/dirs lists.
    """
    print("Running validation")
    required_files = [input_file]
    required_dirs = [output_dir]
    for file_path in required_files:
        if not os.path.isfile(file_path): ""
        raise RuntimeError("Unable to find file: {}".format(file_path))


for dir in required_dirs:
    if not os.path.isdir(dir):
        raise RuntimeError("Unable to find directory: {}".format(dir))
# Skip run if Event workspace
enginx_ws = Load(input_file)
workspace_type = str(type(enginx_ws))
if 'Event' in workspace_type:
    raise RuntimeError('Skip: Event mode currently not supported on EnginX')
print("Validation successful")


def main(input_file, output_dir):
    """
    Autoreduction main function
    ---------------------------

    Function to strip input file down to run-number and begin reduction.

    @param input_file :: path to the file to reduce.
    @param output_dir :: path ot the folder to output to.

    """
    # some files are not there when they are being read,
    # hence introduce a sleep to ensure files are copied over in time.
    time.sleep(20)
    validate(input_file, output_dir)

    # Ensure that the variables for reduce_var.py are of the correct type
    basic_params = _cast_string_to_None(web_var.standard_vars)
    advanced_params = _cast_string_to_None(web_var.advanced_vars)

    # Get the run number from the full file path
    input_run = _strip_run_number(input_file)

    # Ensure the grouping file is where we expect and we have permission to access it
    grouping_file_location = "/isis/NDXENGINX/user/scripts/autoreduction/EnginX_grouping.cal"
    grouping_file = grouping_file_location if basic_params['grouping_file'] is True else None

    # Run EnginX reduction with reduce_vars.py parameters
    Enginx.main(vanadium_run=advanced_params['vanadium'],
                user="autoreduce",
                focus_run=input_run,
                crop_type=basic_params['crop_type'],
                crop_on=basic_params['crop_on'],
                grouping_file=basic_params['grouping_file'],
                force_vanadium=advanced_params['force_vanadium'],
                force_cal=advanced_params['force_calibration'],
                pre_process_run=advanced_params['pre_process_run'],
                params=advanced_params['params'],
                time_period=advanced_params['time_period'],
                ceria_run=advanced_params['ceria_run'],
                user_struct=False,
                directory=output_dir)


def _strip_run_number(input_file):
    """
    Remove the run number from the file path to the run file
    """
    # get the file name from the path
    file_name = input_file.split("/")[-1]
    # get the run number from the file name
    input_run = file_name.replace("ENGINX", "").strip("0").split(".")[0]
    return input_run


def _cast_string_to_None(dictionary):
    """
    Ensure that parameters that are string type None get cast to NoneType
    """
    for key, value in dictionary.items():
        if value == 'None':
            dictionary[key] = None
    return dictionary


if __name__ == "__main__":
    main("test", "test")
