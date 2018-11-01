"""
Creates a database session for the reduction database
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Table, join
from sqlalchemy.orm import sessionmaker, relationship, column_property

from utils.settings import MYSQL_SETTINGS
from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException


class DatabaseClient(AbstractClient):
    """
    Single access point for the mysql database
    """

    def __init__(self, credentials=None):
        if not credentials:
            credentials = MYSQL_SETTINGS
        super(DatabaseClient, self).__init__(credentials)
        self._connection = None
        self._meta_data = None
        self._engine = None

    def connect(self):
        """
        Get the connection to the database service
        :return: The connection to the database
        """
        if self._connection is None:
            connect_string = self.credentials.get_full_connection_string()
            self._engine = create_engine(connect_string, pool_recycle=280)
            self._meta_data = MetaData(self._engine)
            session = sessionmaker(bind=self._engine)
            self._connection = session()
            self._test_connection()
            return self._connection
        return self._connection

    def _test_connection(self):
        """
        Ensure that the connection has been established
        :return: True if connection is establish
        """
        try:
            self._connection.execute('SELECT 1').fetchall()
        # pylint:disable=broad-except
        except Exception as exp:
            # The original exception appears to be wrapped in a different exception
            # as such it is not being consistently caught so we should check
            # the exception name instead
            if type(exp).__name__ == 'OperationalError':
                raise ConnectionException("MySQL")
            else:
                # re-raise the error if it's something we do not expect
                raise
        return True

    def get_connection(self):
        """
        Retrieve the connection object.
        :return: SQLAlchemy session
        """
        return self._connection

    def disconnect(self):
        """
        Close the connection and reset variables
        """
        self._connection.close()
        self._connection = None
        self._meta_data = None
        self._engine = None

    # ======================== Tables for database access ============================== #
    def instrument(self):
        """
        :return: Instrument Table to replicate what we expect in the database
        """
        # pylint: disable=too-few-public-methods
        class Instrument(declarative_base()):
            """
            Table for reduction_viewer_instrument entity
            """
            __table__ = Table('reduction_viewer_instrument',
                              self._meta_data, autoload=True,
                              autoload_with=self._engine)
        return Instrument

    def reduction_run(self):
        """
        :return: ReductionRun Table to replicate what we expect in the database
        """
        # pylint: disable=too-few-public-methods
        class ReductionRun(declarative_base()):
            """
            Table for reduction_viewer_reductionrun entity
            """
            __table__ = Table('reduction_viewer_reductionrun',
                              self._meta_data, autoload=True,
                              autoload_with=self._engine)
            instrument = relationship(self.instrument(),
                                      foreign_keys='ReductionRun.instrument_id')
        return ReductionRun
