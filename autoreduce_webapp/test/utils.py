import os, logging, shutil
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, REDUCTION_DIRECTORY
from reduction_viewer.utils import InstrumentUtils, StatusUtils
from reduction_viewer.models import Experiment, ReductionRun
from reduction_variables.models import RunVariable
logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),level=LOG_LEVEL, format=u'%(message)s',)


def copyScripts(name):
    reduce_script = os.path.join(os.path.dirname(__file__), '../', 'test_files',name,'reduce.py')
    reduce_vars = os.path.join(os.path.dirname(__file__), '../', 'test_files',name,'reduce_vars.py')
    
    valid_reduction_file = REDUCTION_DIRECTORY % name
    if not os.path.exists(valid_reduction_file):
        os.makedirs(valid_reduction_file)
    file_path = os.path.join(valid_reduction_file, 'reduce.py')
    if not os.path.isfile(file_path):
        shutil.copyfile(reduce_script, file_path)
    file_path = os.path.join(valid_reduction_file, 'reduce_vars.py')
    if not os.path.isfile(file_path):
        shutil.copyfile(reduce_vars, file_path)
        

def removeScripts(name):
    directory = REDUCTION_DIRECTORY % name
    logging.warning("About to remove %s" % directory)
    if os.path.exists(directory):
        shutil.rmtree(directory)
        

def getValidScript(name):
    reduction_file = os.path.join(REDUCTION_DIRECTORY % 'valid', name)
    try:
        f = open(reduction_file, 'r')
        script_text = f.read()
        return script_text
    except:
        return None
        
def getReductionRun(with_variables=True):
    instrument = InstrumentUtils().get_instrument('valid')
    experiment = Experiment(reference_number=1)
    experiment.save()
    reduction_run = ReductionRun(instrument=instrument, run_number=1, experiment=experiment, run_version=0, status=StatusUtils().get_queued(), script=getValidScript('reduce.py'))
    reduction_run.save()        

    if with_variables:            
        variable = RunVariable(reduction_run=reduction_run,name='test',value='testvalue1',type='text',is_advanced=False)
        variable.save()
        reduction_run.run_variables.add(variable)

        variable = RunVariable(reduction_run=reduction_run,name='advanced_test',value='testvalue2',type='text',is_advanced=True)
        variable.save()
        reduction_run.run_variables.add(variable)

        reduction_run.save()

    return reduction_run
    
