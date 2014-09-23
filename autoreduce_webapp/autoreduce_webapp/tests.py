from django.test import TestCase
from django.utils import timezone
from settings import LOG_FILE, LOG_LEVEL, ACTIVEMQ, BASE_DIR, REDUCTION_SCRIPT_BASE
import sys, time, logging, os, datetime, json, shutil
logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),level=LOG_LEVEL)
from daemon import Daemon
from queue_processor_daemon import QueueProcessorDaemon
from queue_processor import Client
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_viewer.models import ReductionRun, Instrument, ReductionLocation, Status, Experiment, DataLocation
from reduction_viewer.utils import StatusUtils
from reduction_variables.models import InstrumentVariable, RunVariable, ScriptFile

class QueueProcessorTestCase(TestCase):
    '''
        Insert any data that is needed for tests
    '''
    def setUp(self):
        instrument1, created1 = Instrument.objects.get_or_create(name="ExistingTestInstrument1")
        instrument2, created2 = Instrument.objects.get_or_create(name="InactiveInstrument", is_active=False)
        self.save_dummy_reduce_script("InactiveInstrument")

    '''
        Remove InactiveInstrument dummy script
    '''
    def tearDown(self):
        self.remove_dummy_reduce_script("InactiveInstrument")

    @classmethod
    def setUpClass(cls):
        cls._client = Client(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Autoreduction_QueueProcessor_Test')
        cls._client.connect()
        cls._rb_number = 0
        cls._timeout_wait = 1

    '''
        Insert a reduction run to ensure the QueueProcessor can find one when recieving a topic message
    '''
    def insert_run(self, experiment, run_number=1, run_version=0, instrument="TestInstrument", data="/false/path"):
        ins, created = Instrument.objects.get_or_create(name=instrument)
        run = ReductionRun(run_number=run_number, instrument=ins, experiment=experiment, run_version=run_version, status=StatusUtils().get_queued())
        run.save()
        data_location = DataLocation(file_path=data, reduction_run=run)
        data_location.save()
        return run

    '''
        Check that a reduction run matches the values in the dictionary used to create it
    '''
    def assert_run_match(self, data_dict, reduction_run):
        self.assertEqual(reduction_run.instrument.name, data_dict["instrument"], "Expecting instrument to be %s but was %s" % (data_dict["instrument"], reduction_run.instrument.name))
        self.assertEqual(reduction_run.run_number, data_dict["run_number"], "Expecting run_number to be %s but was %s" % (data_dict["run_number"], reduction_run.run_number))
        self.assertEqual(reduction_run.experiment.reference_number, data_dict["rb_number"], "Expecting rb_number to be %s but was %s" % (data_dict["rb_number"], reduction_run.experiment.reference_number))

    '''
        Get a new RB Number to prevent conflicts
    '''
    def get_rb_number(self):
        self._rb_number -= 1
        return self._rb_number

    '''
        Create dummy variables for a given instrument
    '''
    def create_instrument_variables(self, instrument_name):
        instrument, created = Instrument.objects.get_or_create(name=instrument_name)
        instrument_variables = InstrumentVariable(instrument=instrument, start_run=0,name='TEST_NAME',value='TEST_VALUE', type='String')
        instrument_variables.save()

    '''
        Copy a test reduce.py script to the correct location for use in the tests
    '''
    def save_dummy_reduce_script(self, instrument_name):
        directory = os.path.join(REDUCTION_SCRIPT_BASE, instrument_name)
        test_reduce = os.path.join(os.path.dirname(__file__), '../', 'test_files','reduce.py')
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_path = os.path.join(directory, 'reduce.py')
        if not os.path.isfile(file_path):
            shutil.copyfile(test_reduce, file_path)

    '''
        Remove dummy script file. 
        WARNING!!!! Destructive!!!
    '''
    def remove_dummy_reduce_script(self, instrument_name):
        directory = os.path.join(REDUCTION_SCRIPT_BASE, instrument_name)
        logger.warning("About to remove %s" % directory)
        if os.path.exists(directory):
            shutil.rmtree(directory)

    '''
        Create a new reduction run and check that it auto-creates an instrument when it doesn't exist
    '''
    def test_data_ready_new_instrument(self):
        rb_number = self.get_rb_number()
        instrument_name = "test_data_ready_new_instrument-TestInstrument"
        self.save_dummy_reduce_script(instrument_name)
        try:
            self.assertEqual(Instrument.objects.filter(name=instrument_name).first(), None, "Wasn't expecting to find %s" % instrument_name)
            test_data = {
                "run_number" : 1,
                "instrument" : instrument_name,
                "rb_number" : rb_number,
                "data" : "/false/path",
                "run_version" : 0
            }
            self._client.send('/topic/DataReady', json.dumps(test_data))
            time.sleep(self._timeout_wait)

            experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
            runs = ReductionRun.objects.filter(experiment=experiment, run_number=1)

            self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
            self.assert_run_match(test_data, runs[0])
            self.assertEqual(str(runs[0].status), "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status)
            instrument = Instrument.objects.filter(name=instrument_name).first()
            self.assertNotEqual(instrument, None, "Was expecting to find %s" % instrument_name)
            self.assertTrue(instrument.is_active, "Was expecting instrument to be active")
        finally:
            self.remove_dummy_reduce_script(instrument_name)

    '''
        Create a new reduction run on an instrument that already exists
    '''
    def test_data_ready_existing_instrument(self):
        rb_number = self.get_rb_number()
        instrument_name = "ExistingTestInstrument1"
        self.create_instrument_variables(instrument_name)
        self.assertNotEqual(Instrument.objects.filter(name=instrument_name).first(), None, "Was expecting to find %s" % instrument_name)
        test_data = {
            "run_number" : 1,
            "instrument" : instrument_name,
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/DataReady', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment, run_number=1)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status)
        self.assertNotEqual(Instrument.objects.filter(name=instrument_name).first(), None, "Was expecting to find %s" % instrument_name)

    '''
        Create a new reduction run on an instrument that already exists
    '''
    def test_data_ready_inactive_instrument(self):
        rb_number = self.get_rb_number()
        instrument_name = "InactiveInstrument"
        instrument = Instrument.objects.filter(name=instrument_name).first()
        self.assertNotEqual(instrument, None, "Was expecting to find %s" % instrument_name)
        self.assertFalse(instrument.is_active, "Was expecting %s to be inactive" % instrument_name)
        test_data = {
            "run_number" : 1,
            "instrument" : instrument_name,
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/DataReady', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment, run_number=1)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status)
        instrument = Instrument.objects.filter(name=instrument_name).first()
        self.assertNotEqual(instrument, None, "Was expecting to find %s" % instrument_name)
        self.assertTrue(instrument.is_active, "Was expecting %s to be active" % instrument_name)

    '''
        Create two new reduction runs for the same experiment
    '''
    def test_data_ready_multiple_runs(self):
        rb_number = self.get_rb_number()
        instrument_name = "test_data_ready_multiple_runs-TestInstrument"
        self.save_dummy_reduce_script(instrument_name)
        try:
            test_data_run_1 = {
                "run_number" : 1,
                "instrument" : instrument_name,
                "rb_number" : rb_number,
                "data" : "/false/path",
                "run_version" : 0
            }
            test_data_run_2 = {
                "run_number" : -2,
                "instrument" : instrument_name,
                "rb_number" : rb_number,
                "data" : "/false/path",
                "run_version" : 0
            }
            self._client.send('/topic/DataReady', json.dumps(test_data_run_1))
            self._client.send('/topic/DataReady', json.dumps(test_data_run_2))
            time.sleep(self._timeout_wait)

            experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
            runs = ReductionRun.objects.filter(experiment=experiment)

            self.assertEqual(len(runs), 2, "Should only return 2 reduction runs but returned %s" % len(runs))
            self.assert_run_match(test_data_run_1, runs[0])
            self.assertEqual(str(runs[0].status), "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status)
            self.assert_run_match(test_data_run_2, runs[1])
            self.assertEqual(str(runs[1].status), "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[1].status)
        finally:
            self.remove_dummy_reduce_script(instrument_name)
        
    '''
        Change an existing reduction run from Queued to Started
    '''
    def test_reduction_started_reduction_run_exists(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        self.insert_run(run_number=1, instrument="test_reduction_started-TestInstrument", experiment=experiment)

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_started-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Processing", "Expecting status to be 'Processing' but was '%s'" % runs[0].status)

    '''
        Attempt to change a non-existing reduction run from Queued to Started
    '''
    def test_reduction_started_reduction_run_doesnt_exist(self):
        rb_number = self.get_rb_number()
        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_started-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 0, "Shouldn't return any reduction runs but returned %s" % len(runs))

    '''
        Attempt to (incorrectly) start an already started reduction run
    '''
    def test_reduction_started_reduction_run_already_started(self):
        rb_number = self.get_rb_number()
        started_time = timezone.now().replace(microsecond=0)
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = self.insert_run(run_number=1, instrument="test_reduction_started_reduction_run_already_started-TestInstrument", experiment=experiment)
        run.status = StatusUtils().get_processing()
        run.started = started_time
        run.save()

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_started_reduction_run_already_started-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Processing", "Expecting status to be 'Processing' but was '%s'" % runs[0].status)
        self.assertEqual(runs[0].started, started_time, "Started time should not have been updated")

    '''
        Attempt to (incorrectly) start a reduction run that has already completed
    '''
    def test_reduction_started_reduction_run_already_completed(self):
        rb_number = self.get_rb_number()
        started_time = timezone.now().replace(microsecond=0)
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = self.insert_run(run_number=1, instrument="test_reduction_started_reduction_run_already_completed-TestInstrument", experiment=experiment)
        run.status = StatusUtils().get_completed()
        run.started = started_time
        run.save()

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_started_reduction_run_already_completed-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Completed", "Expecting status to be 'Completed' but was '%s'" % runs[0].status)
        self.assertEqual(runs[0].started, started_time, "Started time should not have been updated")

    '''
        Re-start a reduction run than had previously shown an error
    '''
    def test_reduction_started_reduction_run_error(self):
        rb_number = self.get_rb_number()
        started_time = timezone.now().replace(microsecond=0)
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = self.insert_run(run_number=1, instrument="test_reduction_started_reduction_run_error-TestInstrument", experiment=experiment)
        run.status = StatusUtils().get_error()
        run.started = started_time
        run.save()
        #Sleep so started time can change
        time.sleep(self._timeout_wait)

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_started_reduction_run_error-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Processing", "Expecting status to be 'Processing' but was '%s'" % runs[0].status)
        self.assertNotEqual(runs[0].started, started_time, "Started time should have been updated")

    '''
        Change a started reduction run to completed
    '''
    def test_reduction_complete_reduction_run_exists(self):
        rb_number = self.get_rb_number()
        started_time = timezone.now().replace(microsecond=0)
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = self.insert_run(run_number=1, instrument="test_reduction_complete_reduction_run_exists-TestInstrument", experiment=experiment)
        run.status = StatusUtils().get_processing()
        run.started = started_time
        run.save()

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_complete_reduction_run_exists-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Completed", "Expecting status to be 'Completed' but was '%s'" % runs[0].status)
        self.assertNotEqual(runs[0].finished, None, "Expected the reduction run to have a finished timestamp")

    '''
        Attempt to complete a reduction run that doesn't exist
    '''
    def test_reduction_complete_reduction_run_doesnt_exists(self):
        rb_number = self.get_rb_number()

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_complete_reduction_run_doesnt_exists-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 0, "Should only return 0 reduction runs but returned %s" % len(runs))

    '''
        Attempt to (incorrectly) complete a queued reduction run
    '''
    def test_reduction_complete_reduction_run_queued(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = self.insert_run(run_number=1, instrument="test_reduction_complete_reduction_run_queued-TestInstrument", experiment=experiment)
        run.status = StatusUtils().get_queued()
        run.save()

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_complete_reduction_run_queued-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status)
        self.assertEqual(runs[0].started, None, "Not expecting the reduction run to have a started timestamp")
        self.assertEqual(runs[0].finished, None, "Not expecting the reduction run to have a finished timestamp")

    '''
        Attempt to (incorrectly) complete a completed reduction run
    '''
    def test_reduction_complete_reduction_run_complete(self):
        rb_number = self.get_rb_number()
        started_time = timezone.now().replace(microsecond = 0)
        finished_time = timezone.now().replace(microsecond = 0)
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = self.insert_run(run_number=1, instrument="test_reduction_complete_reduction_run_complete-TestInstrument", experiment=experiment)
        run.status = StatusUtils().get_completed()
        run.started = started_time
        run.finished = finished_time
        run.save()

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_complete_reduction_run_complete-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Completed", "Expecting status to be 'Completed' but was '%s'" % runs[0].status)
        self.assertEqual(runs[0].started, started_time, "Not expecting the reduction run start to have changed. Was expecting %s but got %s" % (started_time, runs[0].started))
        self.assertEqual(runs[0].finished, finished_time, "Not expecting the reduction run finish to have changed. Was expecting %s but got %s" % (finished_time, runs[0].finished))

    '''
        Attempt to (incorrectly) complete a reduction run with an error
    '''
    def test_reduction_complete_reduction_run_error(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = self.insert_run(run_number=1, instrument="test_reduction_complete_reduction_run_error-TestInstrument", experiment=experiment)
        run.status = StatusUtils().get_error()
        run.save()

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_complete_reduction_run_error-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Error", "Expecting status to be 'Error' but was '%s'" % runs[0].status)
        self.assertEqual(runs[0].started, None, "Not expecting the reduction run to have a started timestamp")
        self.assertEqual(runs[0].finished, None, "Not expecting the reduction run to have a finished timestamp")

    '''
        Set a reduction run as having an error
    '''
    def test_reduction_error_reduction_run_exists(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        self.insert_run(run_number=1, instrument="test_reduction_error_reduction_run_exists-TestInstrument", experiment=experiment)
        error_message = "We have an error here"

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_error_reduction_run_exists-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0,
            "message" : error_message
        }
        self._client.send('/topic/ReductionError', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Error", "Expecting status to be 'Error' but was '%s'" % runs[0].status)
        self.assertEqual(runs[0].message, error_message, "Expecting the error message to be populated")

    '''
        Set a reduction run as having an error
    '''
    def test_reduction_error_reduction_run_exists_no_message(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        self.insert_run(run_number=1, instrument="test_reduction_error_reduction_run_exists_no_message-TestInstrument", experiment=experiment)

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_error_reduction_run_exists_no_message-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionError', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(str(runs[0].status), "Error", "Expecting status to be 'Error' but was '%s'" % runs[0].status)
        self.assertEqual(runs[0].message, '', "Not expecting the error message to be populated but was '%s'" % runs[0].message)

    '''
        Set a reduction run as having an error
    '''
    def test_reduction_error_reduction_run_doesnt_exists(self):
        rb_number = self.get_rb_number()

        test_data = {
            "run_number" : 1,
            "instrument" : "test_reduction_error_reduction_run_doesnt_exists-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/topic/ReductionError', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 0, "Should only return 0 reduction runs but returned %s" % len(runs))
