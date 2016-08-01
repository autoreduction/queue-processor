import os, logging, shutil
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, REDUCTION_DIRECTORY
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