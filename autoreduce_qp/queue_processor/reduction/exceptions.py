# ############################################################################ #
# Autoreduction Repository :
# https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
"""Exceptions that may be raised when performing a reduction."""


class DatafileError(Exception):
    """Exception when there is an issue reading a datafile."""


class ReductionScriptError(Exception):
    """
    Exception when an unhandled exception is produced within the reduction
    script.
    """
