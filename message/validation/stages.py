# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Combination of validation checks to be performed on the Message at each stage of the pipeline
"""
from message.validation.validators import validate_run_number, validate_instrument
from message.validation.process import check_validity_dict


def validate_data_ready(message):
    """
    Assert a message is ready to be passed to the /DataReady queue
    :param message: A message object to be validated
    :return: True if valid
    """
    validity_dict = {
        'run_number': validate_run_number(message.run_number),
        'instrument': validate_instrument(message.instrument),
        'rb_number': isinstance(message.rb_number, str) or isinstance(message.rb_number, int),
        'started_by': isinstance(message.started_by, int),
        'file_path': isinstance(message.data, str),
        'facility': isinstance(message.facility, str)
    }
    return check_validity_dict(validity_dict)
