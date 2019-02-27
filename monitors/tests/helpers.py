# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Collection of test helpers to be used with the End of Run Monitor tests
"""
import ast

import stomp

from utils.settings import ACTIVEMQ_SETTINGS


class TestListener(stomp.ConnectionListener):
    """
    Class for consuming and recording the most recent message sent to activemq
    """
    message = None

    def on_message(self, headers, body):
        """
        Convert message into dictionary and update cached message
        :param headers: message header (discarded in this case)
        :param body: String version of run information dictionary
        """
        message_dictionary = ast.literal_eval(body)
        self.message = message_dictionary


def create_connection(listener):
    """
    Creates a connection to ActiveMQ with a listener
    :param listener: The listener for the ActiveMQ connection
    :return: The connection
    """
    connection = stomp.Connection([(ACTIVEMQ_SETTINGS.host, ACTIVEMQ_SETTINGS.port)])
    connection.set_listener('TestListener', listener)
    connection.start()
    connection.connect()
    connection.subscribe(destination=ACTIVEMQ_SETTINGS.data_ready, id='1')
    return connection
