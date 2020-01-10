# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Functionality to remove a reduction run from the database
"""

import  unittest

# from scripts.system_performance.system_performance import DateInCycle


class TestRunStatistics(unittest.TestCase):
    """
    Unit tests for run statistics of Autoreduction
    pre-logic data preparations for system performance MySQL queries
    """

    def setUp(self):
        """
        Setup:
        cycle dataframe
        cycle row from dataframe
        list containing index, start end
        """
        pass

    def tearDown(self):
        """

        """
        pass

    def testcycle_dates(self):
        """
        Assert if index, cycle start and end are returned in a list
        """
        pass

    def testin_cycle(self):
        """
        Assert return current cycle or previous cycle
        Assert if current date is in a cycle or or between cycles
        """
        pass

    def testdate_in_cycle(self):
        """
        Assert correct index and cycle dates are returned
        """
        pass

    def testrun_fail_count(self):
        """
        Assert run and fail count values are as expected in list for
        :param [total run, total fail]
        """
        pass
