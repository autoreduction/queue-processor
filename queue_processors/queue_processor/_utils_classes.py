# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
"""
Contains various Utility classes for accessing the DB / message queue
which is used by the message handler
"""
from typing import NamedTuple

from queue_processors.queue_processor.queueproc_utils.messaging_utils import \
    MessagingUtils
from queue_processors.queue_processor.queueproc_utils \
    .instrument_variable_utils \
    import InstrumentVariablesUtils
from queue_processors.queue_processor.queueproc_utils.reduction_run_utils \
    import \
    ReductionRunUtils
from queue_processors.queue_processor.queueproc_utils.status_utils import \
    StatusUtils


class _UtilsClasses(NamedTuple):
    """
    Holds various util classes used by the Queue Processor, this can
    be replaced with a mock object at test time if required.
    """
    status: StatusUtils = StatusUtils()
    instrument_variable: InstrumentVariablesUtils = InstrumentVariablesUtils()
    reduction_run: ReductionRunUtils = ReductionRunUtils()
    messaging: MessagingUtils = MessagingUtils()
