# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module that provides error message utils
"""

import logging
import logging.config

from model.database import access as db

from queue_processors.queue_processor.settings import LOGGING

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


def log_error_and_notify(message):
    """
    Helper method to log an error and save a notification
    """
    logger.error(message)
    model = db.start_database().data_model
    notification = model.Notification(is_active=True,
                                      is_staff_only=True,
                                      severity='e',
                                      message=message)
    db.save_record(notification)
