"""
Creates a database session for the reduction database
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, relationship

from EndOfRunMonitor.settings import MYSQL

# pylint: disable=invalid-name
Base = declarative_base()

# Create the connection string for SQLAlchemy
connect_string = 'mysql+mysqldb://' + MYSQL['USER'] + ':' + MYSQL['PASSWD'] + \
                 '@' + MYSQL['HOST'] + '/' + MYSQL['DB']

# Create the engine and the metadata which will be passed to the mapping script
# The pool_recycle will ensure that MySQL will not close this connection if it
# is idle for more than 8 hours.
engine = create_engine(connect_string, pool_recycle=280)
metadata = MetaData(engine)

Session = sessionmaker(bind=engine)
session = Session()


# ========================== Classes for database tables =================================== #
# pylint: disable=too-few-public-methods
class Instrument(Base):
    """
    Table for reduction_viewer_instrument entity
    """
    __table__ = Table('reduction_viewer_instrument',
                      metadata, autoload=True,
                      autoload_with=engine)


# pylint: disable=too-few-public-methods
class ReductionRun(Base):
    """
    Table for reduction_viewer_reductionrun entity
    """
    __table__ = Table('reduction_viewer_reductionrun',
                      metadata, autoload=True,
                      autoload_with=engine)
    instrument = relationship('Instrument',
                              foreign_keys='ReductionRun.instrument_id')
