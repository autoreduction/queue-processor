# ################################################################################
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ################################################################################

import unittest
from unittest import mock


class TestAdmin(unittest.TestCase):

    @mock.patch("django.contrib.admin")
    def test_something(self, admin_mock):
        # This import trigger the code under test
        import autoreduce_webapp.admin as imported_admin

        admin_mock.site.register_called_once_with(imported_admin.UserCache)
        admin_mock.site.register_called_once_with(
            imported_admin.ExperimentCache)
        admin_mock.site.register_called_once_with(
            imported_admin.InstrumentCache)


if __name__ == '__main__':
    unittest.main()
