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
import os

from queue_processors.queue_processor.queueproc_utils.error_message_utils import log_error_and_notify
from queue_processors.queue_processor.settings import REDUCTION_DIRECTORY


def reduction_script_location(instrument_name):
    """ Get reduction script location. """
    return REDUCTION_DIRECTORY % instrument_name


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
        log_error_and_notify("Unable to load reduction script %s due to missing import. (%s)" % (script_path, exp))
        raise
    except SyntaxError:
        log_error_and_notify("Syntax error in reduction script %s" % script_path)
        raise
    except FileNotFoundError as err:
        log_error_and_notify("Reduction script not found at %s" % err.filename)
        raise
