# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for code that generates a working local database for autoredction
"""
import os
import unittest

from unittest.mock import Mock
from sqlalchemy.exc import OperationalError

from build.database.generate_database import (get_test_user_sql, get_sql_from_file,
                                              run_sql)
from build.utils.common import ROOT_DIR


# pylint:disable=missing-docstring
def raise_operational_error(_):
    raise OperationalError(statement='Fail',
                           params=None,
                           orig=None)


# pylint:disable=missing-docstring
class TestGenerateDatabase(unittest.TestCase):

    def test_get_test_user_sql(self):
        # pylint:disable=import-outside-toplevel
        from utils.settings import MYSQL_SETTINGS
        actual = get_test_user_sql()
        expected = "GRANT ALL ON *.* TO '{0}'@'127.0.0.1' IDENTIFIED BY '{1}';\n" \
                   "FLUSH PRIVILEGES;".format(MYSQL_SETTINGS.username, MYSQL_SETTINGS.password)
        self.assertEqual(expected, actual)

    def test_get_sql_from_file(self):
        sql_file = os.path.join(ROOT_DIR, 'build', 'database', 'reset_autoreduction_db.sql')
        actual = get_sql_from_file(sql_file)
        self.assertIn("GRANT ALL PRIVILEGES ON autoreduction.* TO 'test-user'@'127.0.0.1'",
                      actual)
        self.assertIn("DROP DATABASE IF EXISTS autoreduction;", actual)
        self.assertIn("CREATE DATABASE autoreduction;", actual)

    def test_run_sql(self):
        mock_connection = Mock()
        mock_logger = Mock()
        sql_statement = "test statement;"

        self.assertTrue(run_sql(connection=mock_connection,
                                sql=sql_statement,
                                logger=mock_logger))
        mock_connection.commit.assert_called_once()
        mock_connection.execute.assert_called_once_with(sql_statement)

    def test_run_sql_invalid(self):
        mock_connection = Mock()
        mock_connection.execute.side_effect = raise_operational_error
        mock_logger = Mock()

        self.assertFalse(run_sql(connection=mock_connection, sql='', logger=mock_logger))
