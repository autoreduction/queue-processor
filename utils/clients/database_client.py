"""
Creates a database session for the reduction database
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, relationship

from utils.settings import MYSQL


class DatabaseClient(object):

    def __init__(self, user=None, password=None, host=None, database_name=None):
        """
        Initialise variable, if input is None, values from the settings file are used
        """
        self._user = self._use_default_if_none(user, MYSQL['USER'])
        self._password = self._use_default_if_none(password, MYSQL['PASSWD'])
        self._host = self._use_default_if_none(host, MYSQL['HOST'])
        self._database_name = self._use_default_if_none(database_name, MYSQL['DB'])
        self._connection = None
        self._meta_data = None
        self._engine = None

    @staticmethod
    def _use_default_if_none(input_var, default):
        """
        :param input_var: Input to the class (could be None)
        :param default: The default value to use if input_var is None
        """
        if input_var is None:
            return default
        return input_var

    def get_connection(self):
        """
        Get the connection to the database service
        :return: The connection to the database
        """
        if self._connection is None:
            connect_string = 'mysql+mysqldb://%s:%s@%s/%s' % (self._user,
                                                              self._password,
                                                              self._host,
                                                              self._database_name)
            self._engine = create_engine(connect_string, pool_recycle=280)
            self._meta_data = MetaData(self._engine)
            session = sessionmaker(bind=self._engine)
            self._connection = session()
            self._test_connection()
            return self._connection
        return self._connection

    def _test_connection(self):
        try:
            self._connection.execute('SELECT 1').fetchall()
        except Exception as exp:
            # The original exception appears to be wrapped in a different exception
            # as such it is not being consistently caught so we should check the exception name instead
            if type(exp).__name__ is 'OperationalError':
                raise RuntimeError("Unable to connect to database with the credentials provided")
            else:
                # re-raise the error if it's something we do not expect
                raise
        return True

    def stop(self):
        self._connection.close()
        self._connection = None
        self._meta_data = None
        self._engine = None

    def execute_query(self, query):
        if self._connection is not None:
            cursor = self._connection.cursor()
            cursor.execute(query)
            self._connection.commit()

    # ======================== Tables for database access ============================== #
    def instrument(self):
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
