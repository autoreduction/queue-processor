# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test AbstractClient functionality
"""
import unittest

from utils.clients.abstract_client import AbstractClient
from utils.clients.settings.client_settings import ClientSettings


# pylint:disable=missing-docstring
class TestAbstractClient(unittest.TestCase):
    def test_client_settings_init(self):
        """
        Test: A client is created
        When: A class which implements AbstractClient is initiated with a ClientSettings argument
        """
        valid_settings = ClientSettings(username='user', password='pass', host='host', port='123')
        interface = ClientWrapper(credentials=valid_settings)
        self.assertIsNotNone(interface)

    def test_derived_settings_init(self):
        """
        Test: A client is created
        When: A class which implements AbstractClient is initiated with an argument that
        extends ClientSettings
        """

        # pylint:disable=too-few-public-methods
        class DerivedSettings(ClientSettings):
            pass

        derived_settings = DerivedSettings(username='user', password='pass', host='host', port='123')

        interface = ClientWrapper(credentials=derived_settings)
        self.assertIsNotNone(interface)

    def test_invalid_init(self):
        self.assertRaisesRegex(TypeError, "Expected instance of ClientSettings not <class 'int'>", ClientWrapper, 10)
        self.assertRaisesRegex(TypeError, "Expected instance of ClientSettings not <class 'str'>", ClientWrapper,
                               'string')
        self.assertRaisesRegex(TypeError, "Expected instance of ClientSettings not <class 'list'>", ClientWrapper,
                               [1, 2, 3, 4])


class ClientWrapper(AbstractClient):  # pragma: no cover
    """
    Class that implements the AbstractClient.
    This is used for testing AbstractClient.__init__() - specifically, attempting to supply
    invalid ClientSettings objects.
    See use in utils.clients.tests..test_abstract_client.test_invalid_init (above)
    """
    def connect(self):
        pass

    def disconnect(self):
        pass

    def _test_connection(self):
        pass
