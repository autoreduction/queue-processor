#  Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
#  Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
#  SPDX - License - Identifier: GPL-3.0-or-later
#
"""
Module to store autoreduce custom context processors.
"""


def support_email_processor(_):
    """
    Context processor to add support_email to every page for footer and other areas.
    """
    return {"support_email": "isisreduce@stfc.ac.uk"}
