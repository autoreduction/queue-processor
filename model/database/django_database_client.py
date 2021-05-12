# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Creates a database session for the reduction database
"""
from autoreduce_utils.clients.connection_exception import ConnectionException

from model.database import DjangoORM


class DatabaseClient:
    """
    Single access point for the mysql database
    """

    # ORM object that describes the reduction jobs (data) in the database
    data_model = None
    # ORM object that describes the variables relating to reduction jobs in the database
    variable_model = None

    def connect(self):
        """
        Get the connection to the database service and set the model variables
        """
        if not self.data_model and not self.variable_model:
            orm = DjangoORM()
            orm.connect()
            self.data_model = orm.data_model
            self.variable_model = orm.variable_model

    def _test_connection(self):
        """
        Ensure that the connection has been established or raise exception if not
        :return: True if connection is establish
        """
        try:
            self.data_model.Instrument.objects.first()
            self.variable_model.Variable.objects.first()
        # pylint:disable=broad-except
        except Exception as exp:
            raise ConnectionException("MySQL") from exp
        return True

    def disconnect(self):
        """
        Connection can not be closed (will close at runtime end)
        hence we just set models to None
        """
        self.data_model = None
        self.variable_model = None
