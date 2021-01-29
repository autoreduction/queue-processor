# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
"""
This module contains various exceptions that the message handling could
throw to its caller. All logic exceptions inherit from InvalidStateException
so this should be caught as a base case rather than Exception.
"""


class InvalidStateException(Exception):
    """
    Thrown when an invalid state, such as a missing required field,
    is encountered whilst processing a message.
    Using a custom exception means the caller can distinguish between
    implementation errors (e.g. ValueError) and logically invalid states
    """
    def __init__(self, reduction_run, *args) -> None:
        super().__init__(*args)
        self.reduction_run = reduction_run


class MissingReductionRunRecord(InvalidStateException):
    """
    Thrown when a reduction record is expected in the database, but it
    cannot be found.
    """
    def __init__(self, rb_number, run_number, run_version):
        super().__init__("A reduction run could not be found in the database."
                         f" RB Number: {str(rb_number)}, Run Number: {str(run_number)},"
                         f" Run Version: {str(run_version)}")


class MissingExperimentRecord(InvalidStateException):
    """
    Thrown when an experiment record is expected in the database,
    but it cannot be found
    """
    def __init__(self, rb_number, run_number, run_version):
        super().__init__("A Experiment Record could not be found in the database."
                         f" RB Number: {str(rb_number)}, Run Number: {str(run_number)},"
                         f" Run Version: {str(run_version)}")
