from sqlalchemy import Column, Integer, String, Table, ForeignKey, join
from sqlalchemy.orm import relationship, column_property
from base import Base, metadata, engine


# Create all of the classes for all of the needed tables in the autoreduce schema
class Instrument(Base):
    __table__ = Table('reduction_viewer_instrument', metadata, autoload=True, autoload_with=engine)


class Experiment(Base):
    __table__ = Table('reduction_viewer_experiment', metadata, autoload=True, autoload_with=engine)


class Status(Base):
    __table__ = Table('reduction_viewer_status', metadata, autoload=True, autoload_with=engine)


class DataLocation(Base):
    __table__ = Table('reduction_viewer_datalocation', metadata, autoload=True, autoload_with=engine)
    reduction_run = relationship('ReductionRun', foreign_keys='DataLocation.reduction_run_id')


class ReductionRun(Base):
    __table__ = Table('reduction_viewer_reductionrun', metadata, autoload=True, autoload_with=engine)
    instrument = relationship('Instrument', foreign_keys='ReductionRun.instrument_id')
    experiment = relationship('Experiment', foreign_keys='ReductionRun.experiment_id')
    status = relationship('Status', foreign_keys='ReductionRun.status_id')
    data_location = relationship('DataLocation', primaryjoin='(DataLocation.reduction_run_id == ReductionRun.id)')

variable_table = Table('reduction_variables_variable', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('name', String),
                       Column('value', String),
                       Column('type', String),
                       Column('is_advanced', Integer),
                       Column('help_text', String))


class Variable(Base):
    __table__ = Table('reduction_variables_variable', metadata, autoload=True, autoload_with=engine)


# A special class that joins the InstrumentVariable and Variable tables. This means that one can access all parts of
# both tables whilst only needing to produce one object.
class InstrumentJoin(Base):
    instrument_variable_table = Table('reduction_variables_instrumentvariable', metadata,
                                      Column('variable_ptr_id', Integer, ForeignKey('reduction_variables_variable.id'),
                                             primary_key=True),
                                      Column('instrument_id', Integer, ForeignKey('reduction_viewer_instrument.id')),
                                      Column('experiment_reference', Integer),
                                      Column('start_run', Integer),
                                      Column('tracks_script', Integer)
                                      )

    instrument_variable_join = join(variable_table, instrument_variable_table)

    __table__ = instrument_variable_join
    id = column_property(variable_table.c.id, instrument_variable_table.c.variable_ptr_id)
    instrument = relationship('Instrument', foreign_keys='InstrumentJoin.instrument_id')


# A special class that joins the RunVariable and Variable tables. This means that one can access all parts of
# both tables whilst only needing to produce one object.
class RunJoin(Base):
    reduction_variable_table = Table('reduction_variables_runvariable', metadata,
                                     Column('variable_ptr_id',
                                            Integer,
                                            ForeignKey('reduction_variables_variable.id'),
                                            primary_key=True),
                                     Column('reduction_run_id',
                                            Integer,
                                            ForeignKey('reduction_viewer_reductionrun.id')))

    reduction_variable_join = join(variable_table, reduction_variable_table)

    __table__ = reduction_variable_join
    id = column_property(variable_table.c.id, reduction_variable_table.c.variable_ptr_id)
    reduction_run = relationship('ReductionRun', foreign_keys='RunJoin.reduction_run_id')


class InstrumentVariable(Base):
    __table__ = Table('reduction_variables_instrumentvariable', metadata, autoload=True, autoload_with=engine)
    instrument = relationship('Instrument', foreign_keys='InstrumentVariable.instrument_id')
    variable = relationship('Variable', foreign_keys='InstrumentVariable.variable_ptr_id')


class RunVariable(Base):
    __table__ = Table('reduction_variables_runvariable', metadata, autoload=True, autoload_with=engine)
    variable = relationship('Variable', foreign_keys='RunVariable.variable_ptr_id')
    reduction_run = relationship('ReductionRun', foreign_keys='RunVariable.reduction_run_id')


class Notification(Base):
    __table__ = Table('reduction_viewer_notification', metadata, autoload=True, autoload_with=engine)


class ReductionLocation(Base):
    __table__ = Table('reduction_viewer_reductionlocation', metadata, autoload=True, autoload_with=engine)
    reduction_run = relationship('ReductionRun', foreign_keys='ReductionLocation.reduction_run_id')
