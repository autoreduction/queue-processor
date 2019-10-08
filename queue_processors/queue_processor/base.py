# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint: skip-file
"""
Module for connecting to the Database through sqlalchemy.
"""
# pylint: disable=invalid-name
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

# pylint: disable=import-error,no-name-in-module
from queue_processors.queue_processor.settings import MYSQL

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
