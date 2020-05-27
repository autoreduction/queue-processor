# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Creates a database session for the reduction database
"""
import logging

from model.database import DjangoORM
from utils.clients.connection_exception import ConnectionException
from utils.project.static_content import LOG_FORMAT
from utils.project.structure import get_log_file

logging.basicConfig(filename=get_log_file('django_database_client.log'), level=logging.INFO,
                    format=LOG_FORMAT)


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
        except Exception:
            raise ConnectionException("MySQL")
        return True

    def disconnect(self):
        """
        Connection can not be closed (will close at runtime end)
        hence we just set models to None
        """
        self.data_model = None
        self.variable_model = None

    def get_instrument(self, instrument_name, create=False):
        """
        Find the instrument record associated with the name provided in the database
        :param instrument_name: The name of the instrument to search for
        :param create: If True, then create the record if it can not be found in the database
        :return: The instrument object from the database
        """
        instrument_record = self.data_model.Instrument.objects.filter(name=instrument_name).first()
        if not instrument_record and create:
            instrument_record = self.data_model.Instrument(name=instrument_record,
                                                           is_active=True,
                                                           is_paused=False)
            self.save_record(instrument_record)
        return instrument_record

    @staticmethod
    def save_record(record):
        """
        Save a record to the database
        :param record: The record to save
        Note: This is mostly a wrapper to aid unit testing
        """
        record.save()

    def get_reduction_run(self, instrument, run_number):
        """
        Returns a QuerySet of all ReductionRun versions that have the given instrument/run_number
        :param instrument: The name of the instrument to search for
        :param run_number: The run number to search for
        :return: A QuerySet of the ReductionRun records that match the criteria

        Note: The query set could contain multiple records or None
        """
        return self.data_model.ReductionRun.objects \
            .filter(instrument=self.get_instrument(instrument).id) \
            .filter(run_number=run_number)
