from django.test import TestCase
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, REDUCTION_SCRIPT_BASE, BASE_DIR
import logging, os, sys, shutil
logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),level=LOG_LEVEL, format=u'%(message)s',)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_variables.utils import InstrumentVariablesUtils

class InstrumentVariablesUtilsTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    @classmethod
    def setUpClass(cls):
        test_reduce = os.path.join(os.path.dirname(__file__), '../', 'test_files','reduce.py')
        valid_reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, 'valid')
        if not os.path.exists(valid_reduction_file):
            os.makedirs(valid_reduction_file)
        file_path = os.path.join(valid_reduction_file, 'reduce.py')
        if not os.path.isfile(file_path):
            shutil.copyfile(test_reduce, file_path)

        test_reduce = os.path.join(os.path.dirname(__file__), '../', 'test_files','empty_reduce.py')
        empty_reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, 'empty_script')
        if not os.path.exists(empty_reduction_file):
            os.makedirs(empty_reduction_file)
        file_path = os.path.join(empty_reduction_file, 'reduce.py')
        if not os.path.isfile(file_path):
            shutil.copyfile(test_reduce, file_path)
    
    @classmethod
    def tearDownClass(cls):
        directory = os.path.join(REDUCTION_SCRIPT_BASE, 'valid')
        logging.warning("About to remove %s" % directory)
        if os.path.exists(directory):
            shutil.rmtree(directory)
        directory = os.path.join(REDUCTION_SCRIPT_BASE, 'empty_script')
        logging.warning("About to remove %s" % directory)
        if os.path.exists(directory):
            shutil.rmtree(directory)

    def test_get_default_variables_successfull(self):
        variables = InstrumentVariablesUtils().get_default_variables('valid')

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].instrument.name, 'valid', 'Expecting instrument to be "valid" but was %s' % variables[0].instrument)

    def test_get_default_variables_empty(self):
        variables = InstrumentVariablesUtils().get_default_variables('empty_script')

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertEqual(variables, [], 'Expecting an empty array returned')
        
