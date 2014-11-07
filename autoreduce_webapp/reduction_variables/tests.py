from django.test import TestCase
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, REDUCTION_SCRIPT_BASE, BASE_DIR
import logging, os, sys, shutil, imp
logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),level=LOG_LEVEL, format=u'%(message)s',)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_variables.utils import InstrumentVariablesUtils
from reduction_viewer.models import Notification

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

        empty_test_reduce = os.path.join(os.path.dirname(__file__), '../', 'test_files','empty_reduce.py')
        empty_reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, 'empty_script')
        if not os.path.exists(empty_reduction_file):
            os.makedirs(empty_reduction_file)
        file_path = os.path.join(empty_reduction_file, 'reduce.py')
        if not os.path.isfile(file_path):
            shutil.copyfile(empty_test_reduce, file_path)

        duplicate_test_reduce = os.path.join(os.path.dirname(__file__), '../', 'test_files','duplicate_var_reduce.py')
        duplicate_reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, 'duplicate_var')
        if not os.path.exists(duplicate_reduction_file):
            os.makedirs(duplicate_reduction_file)
        file_path = os.path.join(duplicate_reduction_file, 'reduce.py')
        if not os.path.isfile(file_path):
            shutil.copyfile(duplicate_test_reduce, file_path)

        syntax_error_test_reduce = os.path.join(os.path.dirname(__file__), '../', 'test_files','syntax_error_reduce.py')
        syntax_error_reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, 'syntax_error')
        if not os.path.exists(syntax_error_reduction_file):
            os.makedirs(syntax_error_reduction_file)
        file_path = os.path.join(syntax_error_reduction_file, 'reduce.py')
        if not os.path.isfile(file_path):
            shutil.copyfile(syntax_error_test_reduce, file_path)
    
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
        directory = os.path.join(REDUCTION_SCRIPT_BASE, 'duplicate_var')
        logging.warning("About to remove %s" % directory)
        if os.path.exists(directory):
            shutil.rmtree(directory)
        directory = os.path.join(REDUCTION_SCRIPT_BASE, 'syntax_error')
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
        self.assertTrue(len(variables) == 0, 'Expecting an empty array returned')
        
    def test_get_default_variables_duplicate_var_name(self):
        variables = InstrumentVariablesUtils().get_default_variables('duplicate_var')

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertTrue(len(variables) == 2, 'Expecting at 2 variable returned')
        self.assertEqual(variables[0].instrument.name, 'duplicate_var', 'Expecting instrument to be "duplicate_var" but was %s' % variables[0].instrument)

    def test_get_default_variables_syntax_error(self):
        initial_notification = Notification.objects.filter(is_active=True, is_staff_only=True)
        variables = InstrumentVariablesUtils().get_default_variables('syntax_error')
        updated_notification = Notification.objects.filter(is_active=True, is_staff_only=True)

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertTrue(len(variables) == 0, 'Expecting an empty array returned')
        self.assertTrue(len(updated_notification) > len(initial_notification), 'Expecting a notification to be created')

    def test_get_default_variables_missing(self):
        initial_notification = Notification.objects.filter(is_active=True, is_staff_only=True)
        variables = InstrumentVariablesUtils().get_default_variables('missing')
        updated_notification = Notification.objects.filter(is_active=True, is_staff_only=True)

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertEqual(variables, [], 'Expecting an empty array returned')
        self.assertTrue(len(updated_notification) > len(initial_notification), 'Expecting a notification to be created')

    def test_get_default_variables_pass_in_reduce_script(self):
        reduction_file = os.path.join(REDUCTION_SCRIPT_BASE, 'valid', 'reduce.py')
        reduce_script = imp.load_source('reduce_script', reduction_file)
        variables = InstrumentVariablesUtils().get_default_variables('valid', reduce_script)

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].instrument.name, 'valid', 'Expecting instrument to be "valid" but was %s' % variables[0].instrument)