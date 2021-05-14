# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test autoreduce_db.reduction_viewer.models
"""
import unittest

from model.database.django_database_client import DjangoORM


class TestModels(unittest.TestCase):
    """
    Test autoreduce_db.reduction_viewer.models
    """
    def setUp(self):
        self.database = DjangoORM()
        self.database.connect()

    def test_valid_status_model_value(self):
        """
        Test: Valid Status model value is set correctly
        When: Creating new Status model
        """
        actual = self.database.data_model.Status(value='c')
        self.assertEqual('Completed', actual.value_verbose())

    def test_invalid_status_model_value(self):
        """
        Test: Invalid Status model value is not set correctly
        When: Creating new Status model
        """
        actual = self.database.data_model.Status(value='x')
        self.assertRaises(KeyError, actual.value_verbose)
