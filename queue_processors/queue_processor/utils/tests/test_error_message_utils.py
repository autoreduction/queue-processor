# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module that tests error_message_utils
"""

from unittest import mock

from queue_processors.queue_processor.utils.error_message_utils import log_error_and_notify


@mock.patch("queue_processors.queue_processor.utils.error_message_utils.db")
@mock.patch("queue_processors.queue_processor.utils.error_message_utils.logger")
# pylint:disable=invalid-name
def test_log_error_and_notify(logger: mock.Mock, db: mock.Mock):
    """
    Tests logging an error and creating a staff notification
    """
    my_test_message = "TEST MESSAGE"
    log_error_and_notify(my_test_message)
    logger.error.assert_called_once_with(my_test_message)

    mock_model = db.start_database.return_value.data_model

    mock_model.Notification.assert_called_once_with(is_active=True,
                                                    is_staff_only=True,
                                                    severity="e",
                                                    message=my_test_message)

    db.save_record.assert_called_once_with(mock_model.Notification.return_value)
