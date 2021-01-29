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
