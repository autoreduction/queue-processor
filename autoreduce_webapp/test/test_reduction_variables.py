import logging, os, sys, shutil, imp, json
from mock import patch

from django.test import TestCase
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL, REDUCTION_DIRECTORY, BASE_DIR, ACTIVEMQ
logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),level=LOG_LEVEL, format=u'%(message)s',)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)

from reduction_viewer.utils import InstrumentUtils, StatusUtils
from reduction_viewer.models import Notification, ReductionRun, Experiment, DataLocation

from reduction_variables.utils import VariableUtils, InstrumentVariablesUtils, MessagingUtils
from reduction_variables.models import InstrumentVariable, RunVariable

from utils import copyScripts, removeScripts

REDUCTION_SCRIPT_BASE = REDUCTION_DIRECTORY
testInstrument = 'valid'


class InstrumentVariablesUtilsTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    @classmethod
    def setUpClass(cls):
        map(copyScripts, ['valid', 'empty_script', 'duplicate_var_reduce', 'syntax_error'] )
    
    @classmethod
    def tearDownClass(cls):
        map(removeScripts, ['valid', 'empty_script', 'duplicate_var_reduce', 'syntax_error'])
        pass

    def test_get_default_variables_successfull(self):
        variables = InstrumentVariablesUtils().get_default_variables(testInstrument)

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].instrument.name, testInstrument, 'Expecting instrument to be "valid" but was %s' % variables[0].instrument)

    def test_get_default_variables_empty(self):
        variables = InstrumentVariablesUtils().get_default_variables('empty_script')

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertTrue(len(variables) == 0, 'Expecting an empty array returned')
        
    def test_get_default_variables_duplicate_var_name(self):
        variables = InstrumentVariablesUtils().get_default_variables('duplicate_var_reduce')

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertTrue(len(variables) == 2, 'Expecting 2 variables returned')
        self.assertEqual(variables[0].instrument.name, 'duplicate_var_reduce', 'Expecting instrument to be "duplicate_var_reduce" but was %s' % variables[0].instrument)

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
        reduction_file = os.path.join(REDUCTION_SCRIPT_BASE % testInstrument, 'reduce_vars.py')
        reduce_script = open(reduction_file, "r").read()
        variables = InstrumentVariablesUtils().get_default_variables(testInstrument, reduce_script)

        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].instrument.name, testInstrument, 'Expecting instrument to be "valid" but was %s' % variables[0].instrument)

    def test_get_current_script_text_successful(self):
        script_file = os.path.join(REDUCTION_SCRIPT_BASE % testInstrument, 'reduce.py')
        f = open(script_file, 'rb')
        script_binary = f.read()
        script, script_vars = InstrumentVariablesUtils().get_current_script_text(testInstrument)

        self.assertNotEqual(script, None, "Expecting a script to be returned")
        self.assertEqual(script, script_binary, "Expecting files to match")

    def test_get_current_script_text_missing(self):
        script, script_vars = InstrumentVariablesUtils().get_current_script_text('missing')

        self.assertEqual(script, None, "Expecting script to be None")
        self.assertEqual(script_vars, None, "Expecting script_vars to be None")
        
    def test_set_default_instrument_variables_successful(self):
        variables = InstrumentVariablesUtils().set_default_instrument_variables("valid", 1)
        instrument = InstrumentUtils().get_instrument("valid")
        saved_variables = list(InstrumentVariable.objects.filter(instrument=instrument, start_run=1))
        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(saved_variables, None, 'Expecting some variables saved')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertNotEqual(saved_variables, [], 'Expecting some variables saved')
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].instrument.name, testInstrument, 'Expecting instrument to be "valid" but was %s' % variables[0].instrument)
        self.assertEqual(len(variables), len(saved_variables), "Expecting all returned variables to have been saved")
    
    def test_set_default_instrument_variables_no_start_run(self):
        variables = InstrumentVariablesUtils().set_default_instrument_variables("valid", None)
        
        self.assertNotEqual(variables, None, 'Expecting some variables returned')
        self.assertNotEqual(variables, [], 'Expecting some variables returned')
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].start_run, 1, 'Expcting start_run to be set to 1 but was instead %s' % variables[0].start_run)
        
    def test_set_default_instrument_variables_empty(self):
        variables = InstrumentVariablesUtils().set_default_instrument_variables("empty_script", 1)
        instrument = InstrumentUtils().get_instrument("empty_script")
        saved_variables = list(InstrumentVariable.objects.filter(instrument=instrument, start_run=1))
        
        self.assertEqual(variables, [], 'Expecting no variables returned')
        self.assertEqual(saved_variables, [], 'Expecting no variables saved')
        
    def test_get_current_and_upcoming_variables_test_current(self):
        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(testInstrument)

        self.assertNotEqual(current_variables, None, "Expecting some current variables to be returned")
        self.assertNotEqual(current_variables, [], "Expecting some current variables to be returned")
        self.assertTrue(len(current_variables) > 0, 'Expecting at least 1 current variable returned')

    def test_get_current_and_upcoming_variables_test_upcoming(self):
        upcoming = InstrumentVariablesUtils().set_default_instrument_variables(testInstrument, 99999)

        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(testInstrument)

        self.assertNotEqual(upcoming_variables_by_run, None, "Expecting some upcoming variables to be returned")
        self.assertNotEqual(upcoming_variables_by_run, [], "Expecting some upcoming variables to be returned")
        self.assertTrue(len(upcoming_variables_by_run) > 0, 'Expecting at least 1 upcoming variable returned')
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

        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(testInstrument)

        self.assertNotEqual(upcoming_variables_by_experiment, None, "Expecting some upcoming experiment variables to be returned")
        self.assertNotEqual(upcoming_variables_by_experiment, [], "Expecting some upcoming experiment variables to be returned")
        self.assertTrue(len(upcoming_variables_by_experiment) > 0, 'Expecting at least 1 upcoming experiment variable returned')
        
    @patch('autoreduce_webapp.icat_communication.ICATCommunication.get_upcoming_experiments_for_instrument')
    def test_get_current_and_upcoming_variables_test_upcomming_by_experiment_not_in_ICAT(self, mock_icat_call):
        mock_icat_call.return_value = []
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

        current_variables, upcoming_variables_by_run, upcoming_variables_by_experiment = InstrumentVariablesUtils().get_current_and_upcoming_variables(testInstrument)

        self.assertTrue(len(upcoming_variables_by_experiment) == 0, "Expecting no upcoming experiment variables to be returned")
        
    def test_get_variables_for_run_experiment_reference(self):
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

        experiment = Experiment(reference_number=99999)
        reduction_run = ReductionRun(run_number=1, instrument=instrument, experiment=experiment, run_version=1, status=StatusUtils().get_queued())

        variables = InstrumentVariablesUtils().get_variables_for_run(reduction_run)

        self.assertNotEqual(variables, None, "Expecting some variables to be returned")
        self.assertNotEqual(variables, [], "Expecting some variables to be returned")
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].experiment_reference, 99999, "Expecting instrument variables to match with experiment reference number")
    
    def test_get_variables_for_run_run_number(self):
        instrument = InstrumentUtils().get_instrument("valid")
        variable = InstrumentVariable(
                    instrument=instrument, 
                    name="test", 
                    value="test", 
                    is_advanced=False, 
                    type="text",
                    start_run=99999,
                    )
        variable.save()

        experiment = Experiment(reference_number=1)
        reduction_run = ReductionRun(run_number=100000, instrument=instrument, experiment=experiment, run_version=1, status=StatusUtils().get_queued())

        variables = InstrumentVariablesUtils().get_variables_for_run(reduction_run)

        self.assertNotEqual(variables, None, "Expecting some variables to be returned")
        self.assertNotEqual(variables, [], "Expecting some variables to be returned")
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].experiment_reference, None, "Not expecting experiment_reference")
        self.assertEqual(variables[0].start_run, 99999, "Expecting start run to be 99999 but was %s" % variables[0].start_run)
    
    def test_get_variables_for_run_default_variables(self):
        instrument = InstrumentUtils().get_instrument("valid")
        
        experiment = Experiment(reference_number=1)
        reduction_run = ReductionRun(run_number=123, instrument=instrument, experiment=experiment, run_version=1, status=StatusUtils().get_queued())

        variables = InstrumentVariablesUtils().get_variables_for_run(reduction_run)

        self.assertNotEqual(variables, None, "Expecting some variables to be returned")
        self.assertNotEqual(variables, [], "Expecting some variables to be returned")
        self.assertTrue(len(variables) > 0, 'Expecting at least 1 variable returned')
        self.assertEqual(variables[0].experiment_reference, None, "Not expecting experiment_reference")
        self.assertEqual(variables[0].start_run, 1, "Expecting start run to be 1 but was %s" % variables[0].start_run)


class VariableUtilsTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    @classmethod
    def setUpClass(cls):
        pass
    
    @classmethod
    def tearDownClass(cls):
        pass

    def test_wrap_in_type_syntax_text(self):
        result = VariableUtils().wrap_in_type_syntax("test", "text")

        self.assertEqual(result, "'test'", "Expecting result to be 'test' but was %s" % result)

    def test_wrap_in_type_syntax_text_empty(self):
        result = VariableUtils().wrap_in_type_syntax("", "text")

        self.assertEqual(result, "''", "Expecting result to be single quotes")

    def test_wrap_in_type_syntax_number(self):
        result = VariableUtils().wrap_in_type_syntax("123", "number")

        self.assertEqual(result, "123", "Expecting result to be 123 but was %s" % result)

    def test_wrap_in_type_syntax_number_empty(self):
        result = VariableUtils().wrap_in_type_syntax("", "number")

        self.assertEqual(result, "", "Expecting result to be empty but was %s" % result)

    def test_wrap_in_type_syntax_number_text(self):
        result = VariableUtils().wrap_in_type_syntax("test", "number")

        self.assertEqual(result, "", "Expecting result to be empty but was %s" % result)

    def test_wrap_in_type_syntax_boolean_true_lowercase(self):
        result = VariableUtils().wrap_in_type_syntax("true", "boolean")

        self.assertEqual(result, "True", "Expecting result to be True but was %s" % result)
    
    def test_wrap_in_type_syntax_boolean_true_titlecase(self):
        result = VariableUtils().wrap_in_type_syntax("True", "boolean")

        self.assertEqual(result, "True", "Expecting result to be True but was %s" % result)

    def test_wrap_in_type_syntax_boolean_false_lowercase(self):
        result = VariableUtils().wrap_in_type_syntax("false", "boolean")

        self.assertEqual(result, "False", "Expecting result to be False but was %s" % result)
    
    def test_wrap_in_type_syntax_boolean_false_titlecase(self):
        result = VariableUtils().wrap_in_type_syntax("False", "boolean")

        self.assertEqual(result, "False", "Expecting result to be False but was %s" % result)
    
    def test_wrap_in_type_syntax_boolean_invalid(self):
        result = VariableUtils().wrap_in_type_syntax("test", "boolean")

        self.assertEqual(result, "False", "Expecting result to be False but was %s" % result)

    def test_wrap_in_type_syntax_list_text(self):
        result = VariableUtils().wrap_in_type_syntax("this, is, a, list", "list_text")

        self.assertEqual(result, "['this','is','a','list']", "Expecting result to be ['this','is','a','list'] but was %s" % result)

    def test_wrap_in_type_syntax_list_text_empty(self):
        result = VariableUtils().wrap_in_type_syntax("", "list_text")

        self.assertEqual(result, "[]", "Expecting result to be [] but was %s" % result)

    def test_wrap_in_type_syntax_list_text_numbers(self):
        result = VariableUtils().wrap_in_type_syntax("1, 2, 3", "list_text")

        self.assertEqual(result, "['1','2','3']", "Expecting result to be ['1','2','3'] but was %s" % result)

    def test_wrap_in_type_syntax_list_number(self):
        result = VariableUtils().wrap_in_type_syntax("1, 2, 3", "list_number")

        self.assertEqual(result, "[1, 2, 3]", "Expecting result to be [1, 2, 3] but was %s" % result)

    def test_wrap_in_type_syntax_list_number_empty(self):
        result = VariableUtils().wrap_in_type_syntax("", "list_number")

        self.assertEqual(result, "[]", "Expecting result to be [] but was %s" % result)

    def test_wrap_in_type_syntax_list_number_text(self):
        result = VariableUtils().wrap_in_type_syntax("this, is, a, list", "list_number")

        self.assertEqual(result, "[]", "Expecting result to be [] but was %s" % result)

    def test_wrap_in_type_syntax_unknonw_type(self):
        result = VariableUtils().wrap_in_type_syntax("test", "unknown")

        self.assertEqual(result, "test", "Expecting result to be test but was %s" % result)

    def test_wrap_in_type_syntax_non_string_value(self):
        result = VariableUtils().wrap_in_type_syntax(123, "text")

        self.assertEqual(result, "'123'", "Expecting result to be '123' but was %s" % result)

    def test_convert_variable_to_type_text_to_text(self):
        result = VariableUtils().convert_variable_to_type("test", "text")

        self.assertEqual(result, "test", "Expecting result to be test but was %s" % result)        

    def test_convert_variable_to_type_number_to_text(self):
        result = VariableUtils().convert_variable_to_type(123, "text")

        self.assertEqual(result, "123", "Expecting result to be 123 but was %s" % result)

    def test_convert_variable_to_type_boolean_to_text(self):
        result = VariableUtils().convert_variable_to_type(True, "text")

        self.assertEqual(result, "True", "Expecting result to be True but was %s" % result)

    def test_convert_variable_to_type_number_to_number(self):
        result = VariableUtils().convert_variable_to_type(123, "number")

        self.assertEqual(result, 123, "Expecting result to be 123 but was %s" % result)

    def test_convert_variable_to_type_text_to_number(self):
        result = VariableUtils().convert_variable_to_type("123", "number")

        self.assertEqual(result, 123, "Expecting result to be 123 but was %s" % result)

    def test_convert_variable_to_type_text_to_number_float(self):
        result = VariableUtils().convert_variable_to_type("1.23", "number")

        self.assertEqual(result, 1.23, "Expecting result to be 1.23 but was %s" % result)

    def test_convert_variable_to_type_text_to_number_invalid(self):
        result = VariableUtils().convert_variable_to_type("test", "number")

        self.assertEqual(result, None, "Expecting result to be None but was %s" % result)

    def test_convert_variable_to_type_text_to_list_text(self):
        result = VariableUtils().convert_variable_to_type("this, is, a, list", "list_text")

        self.assertEqual(result, ['this', 'is', 'a', 'list'], "Expecting result to be ['this', 'is', 'a', 'list'] but was %s" % result)

    def test_convert_variable_to_type_text_to_list_text_empty(self):
        result = VariableUtils().convert_variable_to_type("", "list_text")

        self.assertEqual(result, [], "Expecting result to be [] but was %s" % result)

    def test_convert_variable_to_type_number_to_list_text(self):
        result = VariableUtils().convert_variable_to_type(123, "list_text")

        self.assertEqual(result, ['123'], "Expecting result to be ['123'] but was %s" % result)

    def test_convert_variable_to_type_text_to_list_number(self):
        result = VariableUtils().convert_variable_to_type("123, 456", "list_number")

        self.assertEqual(result, [123, 456], "Expecting result to be [123, 456] but was %s" % result)

    def test_convert_variable_to_type_text_to_list_number_with_float(self):
        result = VariableUtils().convert_variable_to_type("123, 456, 5.5", "list_number")

        self.assertEqual(result, [123, 456, 5.5], "Expecting result to be [123, 456, 5.5] but was %s" % result)

    def test_convert_variable_to_type_text_to_boolean_true_lowercase(self):
        result = VariableUtils().convert_variable_to_type("true", "boolean")

        self.assertEqual(result, True, "Expecting result to be True but was %s" % result)

    def test_convert_variable_to_type_text_to_boolean_true_titlecase(self):
        result = VariableUtils().convert_variable_to_type("True", "boolean")

        self.assertEqual(result, True, "Expecting result to be True but was %s" % result)

    def test_convert_variable_to_type_text_to_boolean_false_lowercase(self):
        result = VariableUtils().convert_variable_to_type("false", "boolean")

        self.assertEqual(result, False, "Expecting result to be False but was %s" % result)

    def test_convert_variable_to_type_text_to_boolean_false_titlecase(self):
        result = VariableUtils().convert_variable_to_type("False", "boolean")

        self.assertEqual(result, False, "Expecting result to be False but was %s" % result)

    def test_convert_variable_to_type_unknown_type(self):
        result = VariableUtils().convert_variable_to_type("test", "unknown")

        self.assertEqual(result, "test", "Expecting result to be test but was %s" % result)

    def test_get_type_string_text(self):
        result = VariableUtils().get_type_string("test")

        self.assertEqual(result, "text", "Expecting result to be text but was %s" % result)        

    def test_get_type_string_integer(self):
        result = VariableUtils().get_type_string(123)

        self.assertEqual(result, "number", "Expecting result to be number but was %s" % result)

    def test_get_type_string_float(self):
        result = VariableUtils().get_type_string(5.5)

        self.assertEqual(result, "number", "Expecting result to be number but was %s" % result)

    def test_get_type_string_list_text(self):
        result = VariableUtils().get_type_string(["test", "test2"])

        self.assertEqual(result, "list_text", "Expecting result to be list_text but was %s" % result)

    def test_get_type_string_list_number_integer(self):
        result = VariableUtils().get_type_string([1,2,3])

        self.assertEqual(result, "list_number", "Expecting result to be list_number but was %s" % result)

    def test_get_type_string_list_number_float(self):
        result = VariableUtils().get_type_string([1.1,2.2])

        self.assertEqual(result, "list_number", "Expecting result to be list_number but was %s" % result)

    def test_get_type_string_list_number_mixed(self):
        result = VariableUtils().get_type_string([1,2.2,3])

        self.assertEqual(result, "list_number", "Expecting result to be list_number but was %s" % result)

    def test_get_type_string_list_mixed(self):
        result = VariableUtils().get_type_string(["test", 2, 5.5])

        self.assertEqual(result, "list_text", "Expecting result to be list_text but was %s" % result)

    def test_get_type_string_list_mixed_number_first(self):
        result = VariableUtils().get_type_string([2, "test", 5.5])

        self.assertEqual(result, "list_text", "Expecting result to be list_text but was %s" % result)

    def test_get_type_string_boolean_true(self):
        result = VariableUtils().get_type_string(True)

        self.assertEqual(result, "boolean", "Expecting result to be boolean but was %s" % result)

    def test_get_type_string_boolean_false(self):
        result = VariableUtils().get_type_string(False)

        self.assertEqual(result, "boolean", "Expecting result to be boolean but was %s" % result)

    def test_get_type_string_boolean_unknown(self):
        result = VariableUtils().get_type_string({})

        self.assertEqual(result, "text", "Expecting result to be text but was %s" % result)

    def test_get_type_string_boolean_none(self):
        result = VariableUtils().get_type_string(None)

        self.assertEqual(result, "text", "Expecting result to be text but was %s" % result)

class ReductionVariablesUtilsTestCase(TestCase):
    def setUp(self):
        copyScripts(testInstrument)
    
    def tearDown(self):
        removeScripts(testInstrument)
        pass
    
    @classmethod
    def setUpClass(cls):
        test_reduce = os.path.join(os.path.dirname(__file__), '../', 'test_files','reduce.py')
        valid_reduction_file = REDUCTION_SCRIPT_BASE % testInstrument
        if not os.path.exists(valid_reduction_file):
            os.makedirs(valid_reduction_file)
        file_path = os.path.join(valid_reduction_file, 'reduce.py')
        if not os.path.isfile(file_path):
            shutil.copyfile(test_reduce, file_path)

    @classmethod
    def tearDownClass(cls):
        directory = REDUCTION_SCRIPT_BASE % testInstrument
        logging.warning("About to remove %s" % directory)
        if os.path.exists(directory):
            shutil.rmtree(directory)
        pass

    def get_valid_script(self, name):
        reduction_file = os.path.join(REDUCTION_SCRIPT_BASE % testInstrument, name)
        f = open(reduction_file, 'rb')
        script_binary = f.read()
        return script_binary

    def get_reduction_run(self):
        instrument = InstrumentUtils().get_instrument(testInstrument)
        experiment = Experiment(reference_number=1)
        experiment.save()
        reduction_run = ReductionRun(instrument=instrument, run_number=1, experiment=experiment, run_version=0, status=StatusUtils().get_queued())
        reduction_run.save()
        return reduction_run


class MessagingUtilsTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
        
    @classmethod
    def setUpClass(cls):          
        map(copyScripts, ['valid'])
    
    @classmethod
    def tearDownClass(cls):
        map(removeScripts, ['valid'])
        pass
            

    def get_valid_script(self, name):
        reduction_file = os.path.join(REDUCTION_SCRIPT_BASE % testInstrument, name)
        try:
            f = open(reduction_file, 'rb')
            script_binary = f.read()
            return script_binary
        except:
            return None


    def get_reduction_run(self, with_variables=True):
        instrument = InstrumentUtils().get_instrument(testInstrument)
        experiment = Experiment(reference_number=1)
        experiment.save()
        reduction_run = ReductionRun(instrument=instrument, run_number=1, experiment=experiment, run_version=0, status=StatusUtils().get_queued())
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

    def test_MessagingUtils_successful(self):
        reduction_run = self.get_reduction_run()

        data_location = DataLocation(file_path="/test/data/path", reduction_run=reduction_run)
        data_location.save()
        reduction_run.data_location.add(data_location)
        reduction_run.save()

        send_called = [False]

        parent = self

        class mock_client(object):
            def __init__(self, brokers, user, password, topics=None, consumer_name='QueueProcessor', client_only=True, use_ssl=ACTIVEMQ['SSL'], ssl_version=3):
                pass

            def connect(self):
                pass
                
            def stop(self):
                pass

            def send(self, destination, message, persistent='true', priority=4, delay=None):
                send_called[0] = True
                data_dict = json.loads(message)
                parent.assertEqual(destination, '/queue/ReductionPending', "Expecting the destination to be '/queue/ReductionPending' but was '%s'." % destination)
                parent.assertEqual(data_dict['data'], '/test/data/path', "Expecting the data path to be '/test/data/path' but was '%s'." % data_dict['data'])
                parent.assertEqual(data_dict['run_number'], reduction_run.run_number, "Expecting the run number to be '%s' but was '%s'." % (reduction_run.run_number, data_dict['run_number']))
                parent.assertEqual(data_dict['run_version'], reduction_run.run_version, "Expecting the run version to be '%s' but was '%s'." % (reduction_run.run_version, data_dict['run_version']))
                parent.assertEqual(data_dict['instrument'], reduction_run.instrument.name, "Expecting the run number to be '%s' but was '%s'." % (reduction_run.instrument.name, data_dict['instrument']))
                parent.assertNotEqual(data_dict['reduction_arguments'], None, "Expecting to find some arguments")
                parent.assertNotEqual(data_dict['reduction_arguments'], {}, "Expecting to find some arguments")
                parent.assertTrue('standard_vars' in data_dict['reduction_arguments'], "Expecting to find some standard_vars.")
                parent.assertTrue('advanced_vars' in data_dict['reduction_arguments'], "Expecting to find some advanced_vars.")

        with patch('autoreduce_webapp.queue_processor.Client', mock_client):
            MessagingUtils().send_pending(reduction_run)

        self.assertTrue(send_called[0], "Expecting send to be called")

    def test_MessagingUtils_cancel(self):
        reduction_run = self.get_reduction_run()

        data_location = DataLocation(file_path="/test/data/path", reduction_run=reduction_run)
        data_location.save()
        reduction_run.data_location.add(data_location)
        reduction_run.save()

        send_called = [False]

        parent = self

        class mock_client(object):
            def __init__(self, brokers, user, password, topics=None, consumer_name='QueueProcessor', client_only=True, use_ssl=ACTIVEMQ['SSL'], ssl_version=3):  pass
            def connect(self): pass
            def stop(self): pass

            def send(self, destination, message, persistent='true', priority=4, delay=None):
                send_called[0] = True
                data_dict = json.loads(message)
                parent.assertTrue('cancel' in data_dict, "Expecting 'cancel' in message")
                parent.assertEqual(data_dict['cancel'], True, "Expecting 'cancel' to be true")

        with patch('autoreduce_webapp.queue_processor.Client', mock_client):
            MessagingUtils().send_cancel(reduction_run)

        self.assertTrue(send_called[0], "Expecting send to be called")

    def test_MessagingUtils_no_data(self):
        reduction_run = self.get_reduction_run()

        with self.assertRaises(Exception) as e:
            MessagingUtils().send_pending(reduction_run)

        self.assertEqual(e.exception.message, "No data path found for reduction run", "Expecting exception to be raised")
