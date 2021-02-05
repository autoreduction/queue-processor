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

from model.database import access as db

logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


def log_error_and_notify(message):
    """
    Helper method to log an error and save a notification
    """
    logger.error(message)
    model = db.start_database().data_model
    notification = model.Notification(is_active=True, is_staff_only=True, severity='e', message=message)
    db.save_record(notification)
