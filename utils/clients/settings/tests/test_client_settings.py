# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test the ClientSettings package
"""
from unittest import TestCase, mock

from utils.clients.settings.client_settings import ClientSettings


# pylint:disable=missing-docstring
class TestClientSettings(TestCase):
    def test_valid_init(self):
        settings = ClientSettings(username='user', password='pass', host='host', port='123')
        self.assertIsNotNone(settings)
        self.assertEqual(settings.username, 'user')
        self.assertEqual(settings.password, 'pass')
        self.assertEqual(settings.host, 'host')
        self.assertEqual(settings.port, '123')

    def test_invalid_init(self):
        self.assertRaisesRegex(ValueError, "True of type <class 'bool'> is not a string", ClientSettings, 'string',
                               'string', True, 99.99)
        self.assertRaisesRegex(ValueError, "99.99 of type <class 'float'> is not a string", ClientSettings, 'string',
                               'string', 'string', 99.99)

    def test_accepts_mock_types(self):
        settings = ClientSettings(username=mock.Mock(),
                                  password=mock.MagicMock(),
                                  host=mock.NonCallableMock(),
                                  port=mock.Mock())

        self.assertIsNotNone(settings)
        self.assertIsInstance(settings.username, str)
        self.assertIsInstance(settings.password, str)
        self.assertIsInstance(settings.host, str)
        self.assertIsInstance(settings.port, str)
