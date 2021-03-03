# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Generic settings class for client access
"""


class ClientSettings:
    """
    Hold common values for all Settings object
    """

    username = None
    password = None
    host = None
    port = None

    def __init__(self, username, password, host, port):
        self.username = self._attempt_param_cast(username)
        self.password = self._attempt_param_cast(password)
        self.host = self._attempt_param_cast(host)
        self.port = self._attempt_param_cast(port)

    @staticmethod
    def _attempt_param_cast(param):
        """
        Raise exception if param is not string castable
        """
        try:
            # Bool and float values are clearly easy mistakes
            if isinstance(param, (bool, float)):
                raise TypeError()

            # Python: Easier to ask for forgiveness than permission
            # So just attempt a cast to str, don't check if we have a string
            # so we can use mock objects in-lieu
            return str(param)
        except TypeError as exp:
            raise ValueError(f"{param} of type {type(param)} is not a string") from exp
