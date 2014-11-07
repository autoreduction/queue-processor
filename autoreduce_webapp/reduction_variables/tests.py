from django.test import TestCase
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, REDUCTION_SCRIPT_BASE, BASE_DIR
import logging, os, sys, shutil, imp
logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),level=LOG_LEVEL, format=u'%(message)s',)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_variables.utils import InstrumentVariablesUtils
from reduction_viewer.utils import InstrumentUtils
from reduction_viewer.models import Notification
from reduction_variables.models import InstrumentVariable
from mock import patch

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
        initial_notification = list(Notification.objects.filter(is_active=True, is_staff_only=True))
        variables = InstrumentVariablesUtils().get_default_variables('syntax_error')
        updated_notification = list(Notification.objects.filter(is_active=True, is_staff_only=True))

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertTrue(len(variables) == 0, 'Expecting an empty array returned')
        self.assertTrue(len(updated_notification) > len(initial_notification), 'Expecting a notification to be created')

    def test_get_default_variables_missing(self):
        initial_notification = list(Notification.objects.filter(is_active=True, is_staff_only=True))
        variables = InstrumentVariablesUtils().get_default_variables('missing')
        updated_notification = list(Notification.objects.filter(is_active=True, is_staff_only=True))

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

    def test_get_current_script_text_successful(self):
        script_file = os.path.join(REDUCTION_SCRIPT_BASE, 'valid', 'reduce.py')
        f = open(script_file, 'rb')
        script_binary = f.read()
        script = InstrumentVariablesUtils().get_current_script_text('valid')

        self.assertNotEqual(script, None, "Expecting a script to be returned")
        self.assertEqual(script, script_binary, "Expecting files to match")

    def test_get_current_script_text_missing(self):
        script = InstrumentVariablesUtils().get_current_script_text('missing')

        self.assertEqual(script, None, "Expecting script to be None")
        
    def test_set_default_instrument_variables_successful(self):
        variables = InstrumentVariablesUtils().set_default_instrument_variables("valid", 1)
        instrument = InstrumentUtils().get_instrument("valid")
        saved_variables = list(InstrumentVariable.objects.filter(instrument=instrument, start_run=1))
        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(saved_variables, None, 'Expecting some variables saved')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertNotEqual(saved_variables, [], 'Expecting some variables saved')
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].instrument.name, 'valid', 'Expecting instrument to be "valid" but was %s' % variables[0].instrument)
        self.assertTrue(len(variables[0].scripts) == 1, "Expecting to find a script saved")
        self.assertEqual(len(variables), len(saved_variables), "Expecting all returned variables to have been saved")
    
    def test_set_default_instrument_variables_empty(self):
        variables = InstrumentVariablesUtils().set_default_instrument_variables("empty_script", 1)
        instrument = InstrumentUtils().get_instrument("empty_script")
        saved_variables = list(InstrumentVariable.objects.filter(instrument=instrument, start_run=1))
        
        self.assertEqual(variables, None, 'Expecting no variables returned')
        self.assertEqual(saved_variables, None, 'Expecting no variables saved')
        
    def test_get_current_and_upcoming_variables_test_current(self):
        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables('valid')

        self.assertNotEqual(current_variables, None, "Expecting some current variables to be returned")
        self.assertNotEqual(current_variables, [], "Expecting some current variables to be returned")
        self.assertTrue(len(current_variables) > 0, 'Expecting at least 1 current variable returned')

    def test_get_current_and_upcoming_variables_test_upcomming(self):
        upcoming = InstrumentVariablesUtils().set_default_instrument_variables('valid', 99999)

        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables('valid')

        self.assertNotEqual(upcoming_variables_by_run, None, "Expecting some current variables to be returned")
        self.assertNotEqual(upcoming_variables_by_run, [], "Expecting some current variables to be returned")
        self.assertTrue(len(upcoming_variables_by_run) > 0, 'Expecting at least 1 current variable returned')
        self.assertEqual(len(upcoming), len(upcoming_variables_by_run), "Expecting same variables to be returned as created")
    
    @patch('autoreduce_webapp.icat_communication.ICATCommunication.get_upcoming_experiments_for_instrument')
    def test_get_current_and_upcoming_variables_test_upcomming_by_experiment(self, mock_icat_call):
        mock_icat_call.return_value = [99999]
        instrument = InstrumentUtils().get_instrument("valid")
        variable = InstrumentVariable(
                    instrument=instrument, 
                    name="test", 
                    value="test", 
                    is_advanced=False, 
                    type="text",
                    experiment_reference=99999,
                    )
        variable.save()

        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables('valid')

        self.assertNotEqual(upcoming_variables_by_experiment, None, "Expecting some current variables to be returned")
        self.assertNotEqual(upcoming_variables_by_experiment, [], "Expecting some current variables to be returned")
        self.assertTrue(len(upcoming_variables_by_experiment) > 0, 'Expecting at least 1 current variable returned')
        