# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
#!/usr/bin/env python
"""
Django generated file for webapp control
"""
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autoreduce_webapp.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
