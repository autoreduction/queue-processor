# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for custom context processors
"""
from unittest import TestCase

from WebApp.autoreduce_webapp.autoreduce_webapp.context_processors import support_email_processor


class TestContextProcessors(TestCase):
    """
    Test cases for custom context processors
    """
    def test_support_email_processor(self):
        """
        Test: Support email dict returned
        When: support email context processor called.
        """
        self.assertEqual({"support_email": "isisreduce@stfc.ac.uk"},
                         support_email_processor(None))
