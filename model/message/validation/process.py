# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Functions that handle the processing of the validation dictionary
These can be considered helper functions to message.validation.stages
"""
import logging


def check_validity_dict(validity_dict):
    """
    Loop through a dictionary and assert if all are true
    If not log / print those that are false
    :param validity_dict: (dict) of key (name of validity check), values (result of check)
    :return: True if all values in dict are true, else false
    """
    is_valid = True
    for status in validity_dict.values():
        if not status:
            is_valid = False

    if is_valid:
        return True
    logging.error(dict_to_string(validity_dict))
    return False


def dict_to_string(validity_dict):
    """
    create and return a string representation of the validity check
    :param validity_dict: (dict) containing the validity checks
    :return: (str) A string to print
    """
    result = []
    for key, value in validity_dict.items():
        result.append(f"{key} - {value}")
    return ", ".join(result)
