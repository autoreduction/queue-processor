# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Generic client class used as an interface for other classes
"""

from abc import ABCMeta, abstractmethod

from utils.clients.settings.client_settings import ClientSettings


class AbstractClient:
    """
    Abstract class to ensure all Clients must have an init for credentials
    and connect, disconnect and _test_connection functions
    """
    __metaclass__ = ABCMeta

    credentials = None

    def __init__(self, credentials):
        if not isinstance(credentials, ClientSettings):
            raise TypeError("Expected instance of ClientSettings not {}".format(type(credentials)))
        self.credentials = credentials

    @abstractmethod
    def connect(self):
        """ Abstract function for connecting to a service """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def disconnect(self):
        """ Abstract function for disconnecting from a service """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _test_connection(self):
        """ Abstract function to test if a service connection has been made/is active """
        raise NotImplementedError  # pragma: no cover
