"""
Creates a database session for the reduction database
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, relationship

from utils.clients.test_settings import MYSQL

# Create the connection string for SQLAlchemy
DB_CONNECTION_STR = 'mysql+mysqldb://' + MYSQL['USER'] + ':' + MYSQL['PASSWD'] + \
                 '@' + MYSQL['HOST'] + '/' + MYSQL['DB']
ENGINE = create_engine(DB_CONNECTION_STR, pool_recycle=280)
METADATA = MetaData(ENGINE)


# Database set up
def make_db_session():
    """
    Create a database session
    :return: the connection to the database
    """
    session_maker = sessionmaker(bind=ENGINE)
    return session_maker()


# ========================== Classes for database tables =================================== #
# pylint: disable=invalid-name
BASE = declarative_base()


# pylint: disable=too-few-public-methods
class Instrument(BASE):
    """
    Table for reduction_viewer_instrument entity
    """
    __table__ = Table('reduction_viewer_instrument',
                      METADATA, autoload=True,
                      autoload_with=ENGINE)


# pylint: disable=too-few-public-methods
class ReductionRun(BASE):
    """
    Table for reduction_viewer_reductionrun entity
    """
    __table__ = Table('reduction_viewer_reductionrun',
                      METADATA, autoload=True,
                      autoload_with=ENGINE)
    instrument = relationship('Instrument',
                              foreign_keys='ReductionRun.instrument_id')