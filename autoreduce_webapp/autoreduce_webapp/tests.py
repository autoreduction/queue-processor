from django.test import TestCase
from settings import LOG_FILE, LOG_LEVEL, ACTIVEMQ, BASE_DIR
import sys, time, logging, os, datetime, json
logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),level=LOG_LEVEL)
from daemon import Daemon
from queue_processor_daemon import QueueProcessorDaemon
from queue_processor import Client
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_viewer.models import ReductionRun, Instrument, ReductionLocation, Status, Experiment
from reduction_viewer.utils import StatusUtils
from reduction_variables.models import InstrumentVariable, RunVariable, ScriptFile

class QueueProcessorTestCase(TestCase):
    '''
        Insert any data that is needed for tests
    '''
    def setupUp(self):
        instrument1, created = Instrument.objects.get_or_create(name="ExistingTestInstrument1")
        instrument2, created = Instrument.objects.get_or_create(name="InactiveInstrument", is_active=False)

    @classmethod
    def setUpClass(cls):
        logging.info("Starting up QueueProcessorDaemon")
        try:
            daemon = QueueProcessorDaemon('/tmp/QueueProcessorDaemon.pid')
            daemon.start()
        except:
            pass
        cls._client = Client(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Autoreduction_QueueProcessor_Test')
        cls._client.connect()
        cls._rb_number = 0
        cls._timeout_wait = 0.5

    '''
        Insert a reduction run to ensure the QueueProcessor can find one when recieving a topic message
    '''
    def insert_run(rb_number=-1, run_number=-1, run_version=0, instrument="TestInstrument", data="/false/path"):
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = ReductionRun(run_number=run_number, instrument=instrument, experiment=experiment, data=data, run_version=run_version)
        run.save()
        return run

    '''
        Check that a reduction run matches the values in the dictionary used to create it
    '''
    def assert_run_match(data_dict, reduction_run):
        self.assertEqual(reduction_run.instrument, data_dict["instrument"], "Expecting instrument to be %s but was %s" % (reduction_run.instrument, data_dict["instrument"]))
        self.assertEqual(reduction_run.run_number, data_dict["run_number"], "Expecting run_number to be %s but was %s" % (reduction_run.run_number, data_dict["run_number"]))
        self.assertEqual(reduction_run.rb_number, data_dict["rb_number"], "Expecting rb_number to be %s but was %s" % (reduction_run.rb_number, data_dict["rb_number"]))

    '''
        Get a new RB Number to prevent conflicts
    '''
    def get_rb_number(self):
        self._rb_number -= 1
        return self._rb_number

    '''
        Create a new reduction run and check that it auto-creates an instrument when it doesn't exist
    '''
    def test_data_ready_new_instrument(self):
        rb_number = self.get_rb_number()
        instrument_name = "test_data_ready_new_instrument-TestInstrument"
        self.assertEqual(Instrument.objects.filter(name=instrument_name).first(), None, "Wasn't expecting to find %s" % instrument_name)
        test_data = {
            "run_number" : -1,
            "instrument" : instrument_name,
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/DataReady', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment, run_number=-1)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status.value)
        instrument = Instrument.objects.filter(name=instrument_name).first()
        self.assertNotEqual(instrument, None, "Was expecting to find %s" % instrument_name)
        self.assertTrue(instrument.is_active, "Was expecting instrument to be active")

    '''
        Create a new reduction run on an instrument that already exists
    '''
    def test_data_ready_existing_instrument(self):
        rb_number = self.get_rb_number()
        instrument_name = "ExistingTestInstrument1"
        self.assertNotEqual(Instrument.objects.filter(name=instrument_name).first(), None, "Was expecting to find %s" % instrument_name)
        test_data = {
            "run_number" : -1,
            "instrument" : instrument_name,
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/DataReady', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment, run_number=-1)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status.value)
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
            "run_number" : -1,
            "instrument" : instrument_name,
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/DataReady', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment, run_number=-1)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status.value)
        instrument = Instrument.objects.filter(name=instrument_name).first()
        self.assertNotEqual(instrument, None, "Was expecting to find %s" % instrument_name)
        self.assertTrue(instrument.is_active, "Was expecting %s to be active" % instrument_name)

    '''
        Create two new reduction runs for the same experiment
    '''
    def test_data_ready_multiple_runs(self):
        rb_number = self.get_rb_number()
        instrument_name = "test_data_ready_multiple_runs-TestInstrument"
        test_data_run_1 = {
            "run_number" : -1,
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
        self._client.send('/Topic/DataReady', json.dumps(test_data_run_1))
        self._client.send('/Topic/DataReady', json.dumps(test_data_run_2))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 2, "Should only return 2 reduction runs but returned %s" % len(runs))
        self.assert_run_match(test_data_run_1, runs[0])
        self.assertEqual(runs[0].status.value, "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status.value)
        self.assert_run_match(test_data_run_2, runs[1])
        self.assertEqual(runs[1].status.value, "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[1].status.value)
        
    '''
        Change an existing reduction run from Queued to Started
    '''
    def test_reduction_started_reduction_run_exists(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        insert_run(run_number=-1, instrument="test_reduction_started-TestInstrument", experiment=experiment)

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_started-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Processing", "Expecting status to be 'Processing' but was '%s'" % runs[0].status.value)

    '''
        Attempt to change a non-existing reduction run from Queued to Started
    '''
    def test_reduction_started_reduction_run_doesnt_exist(self):
        rb_number = self.get_rb_number()
        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_started-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 0, "Shouldn't return any reduction runs but returned %s" % len(runs))

    '''
        Attempt to (incorrectly) start an already started reduction run
    '''
    def test_reduction_started_reduction_run_already_started(self):
        rb_number = self.get_rb_number()
        started_time = datetime.datetime.now()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = insert_run(run_number=-1, instrument="test_reduction_started_reduction_run_already_started-TestInstrument", experiment=experiment)
        run.status = StatusUtils.get_processing()
        run.started = started_time
        run.save()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_started_reduction_run_already_started-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Processing", "Expecting status to be 'Processing' but was '%s'" % runs[0].status.value)
        self.assertEqual(runs[0].started, started_time, "Started time should not have been updated")

    '''
        Attempt to (incorrectly) start a reduction run that has already completed
    '''
    def test_reduction_started_reduction_run_already_completed(self):
        rb_number = self.get_rb_number()
        started_time = datetime.datetime.now()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = insert_run(run_number=-1, instrument="test_reduction_started_reduction_run_already_completed-TestInstrument", experiment=experiment)
        run.status = StatusUtils.get_completed()
        run.started = started_time
        run.save()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_started_reduction_run_already_completed-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Completed", "Expecting status to be 'Completed' but was '%s'" % runs[0].status.value)
        self.assertEqual(runs[0].started, started_time, "Started time should not have been updated")

    '''
        Re-start a reduction run than had previously shown an error
    '''
    def test_reduction_started_reduction_run_error(self):
        rb_number = self.get_rb_number()
        started_time = datetime.datetime.now()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = insert_run(run_number=-1, instrument="test_reduction_started_reduction_run_error-TestInstrument", experiment=experiment)
        run.status = StatusUtils.get_error()
        run.started = started_time
        run.save()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_started_reduction_run_error-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionStarted', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Processing", "Expecting status to be 'Processing' but was '%s'" % runs[0].status.value)
        self.assertNotEqual(runs[0].started, started_time, "Started time should have been updated")

    '''
        Change a started reduction run to completed
    '''
    def test_reduction_complete_reduction_run_exists(self):
        rb_number = self.get_rb_number()
        started_time = datetime.datetime.now()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = insert_run(run_number=-1, instrument="test_reduction_complete_reduction_run_exists-TestInstrument", experiment=experiment)
        run.status = StatusUtils.get_processing()
        run.started = started_time
        run.save()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_complete_reduction_run_exists-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Completed", "Expecting status to be 'Completed' but was '%s'" % runs[0].status.value)
        self.assertNotEqual(runs[0].finished, None, "Expected the reduction run to have a finished timestamp")

    '''
        Attempt to complete a reduction run that doesn't exist
    '''
    def test_reduction_complete_reduction_run_exists(self):
        rb_number = self.get_rb_number()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_complete_reduction_run_exists-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionComplete', json.dumps(test_data))
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
        run = insert_run(run_number=-1, instrument="test_reduction_complete_reduction_run_queued-TestInstrument", experiment=experiment)
        run.status = StatusUtils.get_queued()
        run.save()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_complete_reduction_run_queued-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Queued", "Expecting status to be 'Queued' but was '%s'" % runs[0].status.value)
        self.assertEqual(runs[0].started, None, "Not expecting the reduction run to have a started timestamp")
        self.assertEqual(runs[0].finished, None, "Not expecting the reduction run to have a finished timestamp")

    '''
        Attempt to (incorrectly) complete a completed reduction run
    '''
    def test_reduction_complete_reduction_run_complete(self):
        rb_number = self.get_rb_number()
        started_time = datetime.datetime.now()
        finished_time = datetime.datetime.now()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = insert_run(run_number=-1, instrument="test_reduction_complete_reduction_run_complete-TestInstrument", experiment=experiment)
        run.status = StatusUtils.get_completed()
        run.started = started_time
        run.finished = finished_time
        run.save()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_complete_reduction_run_complete-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Complete", "Expecting status to be 'Complete' but was '%s'" % runs[0].status.value)
        self.assertEqual(runs[0].started, started_time, "Not expecting the reduction run to have changed")
        self.assertEqual(runs[0].finished, finished_time, "Not expecting the reduction run to have changed")

    '''
        Attempt to (incorrectly) complete a reduction run with an error
    '''
    def test_reduction_complete_reduction_run_error(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        run = insert_run(run_number=-1, instrument="test_reduction_complete_reduction_run_error-TestInstrument", experiment=experiment)
        run.status = StatusUtils.get_error()
        run.save()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_complete_reduction_run_error-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionComplete', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Complete", "Expecting status to be 'Complete' but was '%s'" % runs[0].status.value)
        self.assertEqual(runs[0].started, None, "Not expecting the reduction run to have a started timestamp")
        self.assertEqual(runs[0].finished, None, "Not expecting the reduction run to have a finished timestamp")

    '''
        Set a reduction run as having an error
    '''
    def test_reduction_error_reduction_run_exists(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        insert_run(run_number=-1, instrument="test_reduction_error_reduction_run_exists-TestInstrument", experiment=experiment)
        error_message = "We have an error here"

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_error_reduction_run_exists-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0,
            "message" : error_message
        }
        self._client.send('/Topic/ReductionError', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Error", "Expecting status to be 'Error' but was '%s'" % runs[0].status.value)
        self.assertEqual(runs[0].message, error_message, "Expecting the error message to be populated")

    '''
        Set a reduction run as having an error
    '''
    def test_reduction_error_reduction_run_exists_no_message(self):
        rb_number = self.get_rb_number()
        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        insert_run(run_number=-1, instrument="test_reduction_error_reduction_run_exists_no_message-TestInstrument", experiment=experiment)

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_error_reduction_run_exists_no_message-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionError', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 1, "Should only return 1 reduction run but returned %s" % len(runs))
        self.assert_run_match(test_data, runs[0])
        self.assertEqual(runs[0].status.value, "Error", "Expecting status to be 'Error' but was '%s'" % runs[0].status.value)
        self.assertEqual(runs[0].message, None, "Not expecting the error message to be populated")

    '''
        Set a reduction run as having an error
    '''
    def test_reduction_error_reduction_run_doesnt_exists(self):
        rb_number = self.get_rb_number()

        test_data = {
            "run_number" : -1,
            "instrument" : "test_reduction_error_reduction_run_doesnt_exists-TestInstrument",
            "rb_number" : rb_number,
            "data" : "/false/path",
            "run_version" : 0
        }
        self._client.send('/Topic/ReductionError', json.dumps(test_data))
        time.sleep(self._timeout_wait)

        experiment, created = Experiment.objects.get_or_create(reference_number=rb_number)
        runs = ReductionRun.objects.filter(experiment=experiment)

        self.assertEqual(len(runs), 0, "Should only return 0 reduction runs but returned %s" % len(runs))
