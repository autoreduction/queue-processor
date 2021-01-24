# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing ways to inject the database for testing
"""
from pathlib import Path
from typing import List, Tuple, Any
from xml.etree.ElementTree import parse

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


def parse_dataset(dataset: Path) -> List[Tuple[str, Any]]:
    """
    Return the rows from the resource xml file as a list. Each element in the list will be a tuple
    of the form (table name, {column1: value1, column2....})
    :param dataset: (Path) the path of the dataset xml file
    :return: (List of tuple) The rows of the dataset
    """
    tree = parse(dataset)
    root = tree.getroot()
    rows = []
    for child in root:
        for column in root.iter(child.tag):
            rows.append((column.tag, column.attrib))
    return rows


