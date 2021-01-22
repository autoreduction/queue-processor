# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module that provides script utils
"""
import importlib.util as imp
import io
import os
from queue_processors.queue_processor.queueproc_utils.error_message_utils import log_error_and_notify

import chardet
from queue_processors.queue_processor.settings import REDUCTION_DIRECTORY


def reduction_script_location(instrument_name):
    """ Get reduction script location. """
    return REDUCTION_DIRECTORY % instrument_name


def load_script(path):
    """
    First detect the file encoding using chardet.
    Then load the relevant reduction script and return back the text of the script.
    If the script cannot be loaded, None is returned.
    """
    # Read raw bytes and determine encoding
    f_raw = io.open(path, 'rb')
    encoding = chardet.detect(f_raw.read(32))["encoding"]

    # Read the file in decoded; io is used for the encoding kwarg
    f_decoded = io.open(path, 'r', encoding=encoding)
    script_text = f_decoded.read()
    return script_text


def get_current_script_text(instrument_name):
    """
    Fetches the reduction script and variables script for the given
    instrument, and returns each as a string.
    """
    script_text = load_reduction_script(instrument_name)
    script_vars_text = load_reduction_vars_script(instrument_name)
    return script_text, script_vars_text


def load_reduction_script(instrument_name):
    """ Loads reduction script. """
    return load_script(os.path.join(reduction_script_location(instrument_name), 'reduce.py'))


def load_reduction_vars_script(instrument_name):
    """ Loads reduction variables script. """
    return load_script(os.path.join(reduction_script_location(instrument_name), 'reduce_vars.py'))


def import_module(script_path):
    """
    Takes a python script as a text string, and returns it loaded as a module.
    Failure will return None, and notify.
    """
    # file name without extension
    module_name = os.path.basename(script_path).split(".")[0]
    try:
        spec = imp.spec_from_file_location(module_name, script_path)
        if spec is None:
            raise ImportError(f"Module at {script_path} does not exist.")
        module = imp.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except ImportError as exp:
        log_error_and_notify("Unable to load reduction script %s due to missing import. (%s)" %
                             (script_path, exp))
        raise
    except SyntaxError:
        log_error_and_notify("Syntax error in reduction script %s" % script_path)
        raise
