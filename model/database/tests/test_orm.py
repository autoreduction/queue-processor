# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests to exercise the code responsible for django ORM access
"""
import sys
import unittest
import os

from unittest.mock import patch

from model.database import DjangoORM
from utils.project.structure import get_project_root


class TestDjangoORM(unittest.TestCase):
    def test_add_webapp_path_already_exist(self):
        """
        Test: The webapp path is not added to sys.path
        When: webapp path already exists and add_webapp_path is called
        """
        webapp_path = os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp')
        sys.path.append(webapp_path)
        expected = sys.path.count(webapp_path)
        DjangoORM.add_webapp_path()
        self.assertEqual(expected, sys.path.count(webapp_path))
        sys.path.remove(webapp_path)  # Cleanup test

    def test_add_webapp_path_not_already_exist(self):
        """
        Test: The webapp path is added to sys.path
        When: webapp path does not already exist and add_webapp_path is called
        """
        expected = os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp')
        old_sys_path = sys.path.copy()
        if expected in sys.path:
            # Remove all expected from sys.path
            sys.path = list(filter(lambda a: a != expected, sys.path))

        DjangoORM.add_webapp_path()
        self.assertIn(expected, sys.path)
        sys.path = old_sys_path  # Cleanup test

    def test_add_webapp_path_duplication(self):
        """
        Test: The path is not add more than once to sys.path
        When: add_webapp_path is called more than once
        """
        DjangoORM.add_webapp_path()
        expected = sys.path
        DjangoORM.add_webapp_path()
        self.assertEqual(expected, sys.path)

    def test_get_data_model(self):
        """
        Test: The data model can be accessed
        When: After it is imported
        """
        orm = DjangoORM()
        orm.connect()
        # pylint:disable=protected-access
        model = orm._get_data_model()
        actual = model.Instrument.objects.get_or_create(name='GEM')[0]
        self.assertIsNotNone(actual)
        self.assertEqual(actual.name, 'GEM')
        actual.delete()

    def test_get_variable_model(self):
        """
        Test: The variable model can be accessed
        When: After it is imported
        Note: This will fail if not pointing to the testing database
        """
        orm = DjangoORM()
        orm.connect()
        # pylint:disable=protected-access
        model = orm._get_variable_model()
        actual = model.Variable.objects.create(name='bool_variable', value=True, type="boolean")
        self.assertIsNotNone(actual)
        self.assertEqual(actual.name, 'bool_variable')
        self.assertEqual(actual.type, 'boolean')
        self.assertEqual(actual.value, True)
        actual.delete()

    def test_connect(self):
        """
        Test: The DjangoORM instance is exposed and populated as member variables
        When: calling the connect function
        """
        orm = DjangoORM()
        self.assertTrue(orm.connect())
        self.assertIsNotNone(orm.data_model.Instrument.objects.all())
        self.assertIsNotNone(orm.variable_model.Variable.objects.all())

    @patch('model.database.orm.DjangoORM.data_model')
    def test_failed_connect(self, mock_data):
        """
        Test: False is returned
        When: connect fails to retrieve data (raises an exception)
        """
        mock_data.Instrument.objects.first.side_effect = RuntimeError
        orm = DjangoORM()
        self.assertFalse(orm.connect())
