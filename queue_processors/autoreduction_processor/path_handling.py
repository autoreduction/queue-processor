"""
A set of functions to help with path handling in autoreduction processor
"""
import os

from queue_processors.autoreduction_processor.settings import MISC


def reduction_script_location(instrument_name):
    """ Returns the reduction script location. """
    return MISC["scripts_directory"] % instrument_name


def get_reduction_script(instrument_name):
    """ Returns the path of the reduction script for an instrument. """
    return os.path.join(reduction_script_location(instrument_name), 'reduce.py')


def is_excitations_instrument(instrument):
    """ Check if an instrument string exists in the Excitations instrument list """
    return instrument in MISC["excitation_instruments"]


def manipulate_excitations_output_dir(output_directory):
    """
    Excitations would like to remove the run number folder at the end
    :param output_directory: The current output directory (with run_number)
    :return: output_directory (without run_number)
    """
    # ToDo: Should use split as this function doesn't work if output_directory ends with '/'
    return output_directory[:output_directory.rfind('/') + 1]


def construct_log_directory(base_directory):
    """
    Construct the directory to store the log files
    :param base_directory: The root of the directory tree
    :return: base_directory + /reduction_logs/
    """
    return base_directory + "/reduction_log/"


def construct_log_file_paths(log_directory, rb_number, run_number):
    """
    Create the paths to the log files for mantid and script output
    :param log_directory: root directory where logs are stored
    :param rb_number: RB number of experiment
    :param run_number: Run number of experiment
    :return: Tuple of (script_log, mantid log)
    """
    log_and_err_name = "RB" + rb_number + "Run" + run_number
    script_log = os.path.join(log_directory, log_and_err_name + "Script.out")
    mantid_log = os.path.join(log_directory, log_and_err_name + "Mantid.log")
    return script_log, mantid_log


def construct_file_paths(instrument, rb_number, run_number):
    """
    Construct the output, output log, temp output and temp output log directories
    :return: Tuple of (output_dir, log_dir, temp_output_dir, temp_output_log_dir)
    """
    output_dir = MISC["ceph_directory"] % (instrument, rb_number, run_number)
    if is_excitations_instrument(instrument):
        output_dir = manipulate_excitations_output_dir(output_dir)
    log_dir = construct_log_directory(output_dir)

    temp_output_dir = MISC["temp_root_directory"] + output_dir
    temp_output_log_dir = MISC["temp_root_directory"] + log_dir

    return output_dir, log_dir, temp_output_dir, temp_output_log_dir


def handle_non_overwrite(output_directory):
    """
    Update the expected output path if we do NOT want to overwrite
    :param output_directory: The original output directory
    :return:
    """
    path_parts = output_directory.split('/')
    new_path = '/'
    for part in path_parts:
        if part != 'autoreduced' and part != '':
            new_path = new_path + part + '/'
    maximum = 0
    for folder in os.listdir(new_path):
        if folder.startswith('autoreduced'):
            number = folder.replace('autoreduced', '')
            if number != '':
                number = int(number) + 1
                if number > maximum:
                    maximum = number
            else:
                maximum = 1
    if maximum == 0:
        new_path = new_path + 'autoreduced' + '/'
    else:
        new_path = new_path + 'autoreduced' + str(maximum) + '/'
    return new_path, new_path + 'reduction_log/'
