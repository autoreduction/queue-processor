# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Todo: We need to assess if this is being used and if so what it is doing
"""

import logging
import os
import shutil

from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, TEST_REDUCTION_DIRECTORY
from reduction_viewer.utils import InstrumentUtils, StatusUtils
from reduction_viewer.models import Experiment, ReductionRun
from reduction_variables.models import RunVariable

logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),
                    level=LOG_LEVEL, format=u'%(message)s',)

# pylint:disable=invalid-name
def copyScripts(name):
    """
    Copy test scripts to expected location
    """
    reduce_script = os.path.join(os.path.dirname(__file__), '../', 'test_files',
                                 name, 'reduce.py')
    reduce_vars = os.path.join(os.path.dirname(__file__), '../', 'test_files',
                               name, 'reduce_vars.py')

    valid_reduction_file = TEST_REDUCTION_DIRECTORY % name
    if not os.path.exists(valid_reduction_file):
        os.makedirs(valid_reduction_file)
    file_path = os.path.join(valid_reduction_file, 'reduce.py')
    if not os.path.isfile(file_path):
        shutil.copyfile(reduce_script, file_path)
    file_path = os.path.join(valid_reduction_file, 'reduce_vars.py')
    if not os.path.isfile(file_path):
        shutil.copyfile(reduce_vars, file_path)


def removeScripts(name):
    """
    Delete test scripts
    """
    directory = TEST_REDUCTION_DIRECTORY % name
    logging.warning("About to remove %s", directory)
    if os.path.exists(directory):
        shutil.rmtree(directory)


def getValidScript(name):
    """
    return contents on reduction file
    """
    reduction_file = os.path.join(TEST_REDUCTION_DIRECTORY % 'valid', name)
    try:
        red_file = open(reduction_file, 'r')
        script_text = red_file.read()
        return script_text
    # pylint:disable=bare-except
    except:
        return None


def getReductionRun(with_variables=True):
    """
    Get a reduction run from the django model
    """
    instrument = InstrumentUtils().get_instrument('valid')
    experiment = Experiment(reference_number=1)
    experiment.save()
    reduction_run = ReductionRun(instrument=instrument, run_number=1, experiment=experiment,
                                 run_version=0, status=StatusUtils().get_queued(),
                                 script=getValidScript('reduce.py'))
    reduction_run.save()

    if with_variables:
        variable = RunVariable(reduction_run=reduction_run, name='test', value='testvalue1',
                               type='text', is_advanced=False)
        variable.save()
        # pylint:disable=no-member
        reduction_run.run_variables.add(variable)

        variable = RunVariable(reduction_run=reduction_run, name='advanced_test',
                               value='testvalue2', type='text', is_advanced=True)
        variable.save()
        reduction_run.run_variables.add(variable)

        reduction_run.save()

    return reduction_run
