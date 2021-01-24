# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing ways to inject the database for testing
"""
import pymysql

from utils.settings import get_str
def get_connection() -> pymysql.Connection:
    """
    Return a PyMySql connection object for querying the database
    :returns: (Connection) The PyMySql Connection object.

    """
    return pymysql.connect(host=get_str("DATABASE", "host"),
                           user=get_str("DATABASE", "user"),
                           password=get_str("DATABASE", "password"),
                           database=get_str("DATABASE", "name"),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
