# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Generic settings class for client access
"""


# pylint:disable=too-few-public-methods
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
        Raise exception if param is not a string else return param
        """
        if not isinstance(param, str):
            raise ValueError("{0} of {1} is not a string".format(param, type(param)))
        return param
