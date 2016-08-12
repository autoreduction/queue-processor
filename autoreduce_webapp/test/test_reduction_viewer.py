import logging, os
from mock import patch

from django.test import TestCase 
from autoreduce_webapp.settings import LOG_FILE, LOG_LEVEL
logging.basicConfig(filename=LOG_FILE.replace('.log', '.test.log'),level=LOG_LEVEL, format=u'%(message)s',)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from utils import copyScripts, removeScripts, getReductionRun, getValidScript

from reduction_variables.models import RunVariable
from reduction_variables.utils import VariableUtils, InstrumentVariablesUtils

from reduction_viewer.models import Instrument, Experiment, ReductionRun
from reduction_viewer.utils import StatusUtils, InstrumentUtils, ReductionRunUtils


class StatusUtilsTestCase(TestCase):
    def test_get_statuses(self):
        statusList = [ ("Error", "get_error")
                     , ("Completed", "get_completed")
                     , ("Processing", "get_processing")
                     , ("Queued", "get_queued")
                     , ("Skipped", "get_skipped")
                     ]
        statuses = []
                     
        for statusValue, utilsMember in statusList:
            # e.g., make sure StatusUtils().get_error exists, and that StatusUtils().get_error().value == "Error"
            self.assertTrue(hasattr(StatusUtils(), utilsMember), "Expected StatusUtils() to have %s" % utilsMember)
            statusObject = getattr(StatusUtils(), utilsMember)()
            
            self.assertNotEqual(statusObject, None, "Expected a status object to be returned from %s" % utilsMember)
            self.assertEqual(statusObject.value, statusValue, "Expected call to %s to return Status with value %s" % (utilsMember, statusValue))
            
            statuses.append(statusObject)
            
        self.assertEqual(len(list(set(statuses))), len(statuses), "Expected all statuses to be unique")

        
        
class InstrumentUtilsTestCase(TestCase):
    def test_get_instrument_create_new_instrument(self):
        newName = "new_instrument_4785937498"
        instrumentObject = InstrumentUtils().get_instrument(newName)
        self.assertNotEqual(instrumentObject, None, "Expected an instrument object")
        self.assertEqual(instrumentObject.name, newName, "Expected the instrument to be named %s, was %s" % (newName, instrumentObject.name))
        
    def test_get_instrument_existing_instrument(self):
        newName = "new_instrument_7219834839"
        newInstrument, created = Instrument.objects.get_or_create(name=newName)
        
        instrumentObject = InstrumentUtils().get_instrument(newName)
        self.assertEqual(instrumentObject, newInstrument, "Expected instrument objects to match")
        
    def test_get_instrument_existing_instrument_case_insensitive(self):
        newName =   "new_instrument_3128908328"
        casedName = "neW_InstrumEnt_3128908328"
        newInstrument, created = Instrument.objects.get_or_create(name=newName)
        
        instrumentObject = InstrumentUtils().get_instrument(casedName)
        self.assertEqual(instrumentObject, newInstrument, "Expected instrument objects to match")
        
        
        
class ReductionRunUtilsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        map(copyScripts, ['valid'])
        cls.run_number = 0
    
    @classmethod
    def tearDownClass(cls):
        map(removeScripts, ['valid'])

    def createReductionRun(self):
        instrument = InstrumentUtils().get_instrument("valid")
        instrument.save()
        experiment = Experiment(reference_number=1)
        experiment.save()
        
        reduction_run = ReductionRun(run_number=self.run_number, instrument=instrument, experiment=experiment, run_version=1, status=StatusUtils().get_queued(), script=getValidScript('reduce.py'))
        self.run_number += 1
        reduction_run.save()
        
        variables = InstrumentVariablesUtils().get_variables_for_run(reduction_run)
        VariableUtils().save_run_variables(variables, reduction_run)
        
        return reduction_run
        
    def createMockMessagingUtils(self):
        self.cancelledRun = None
        parent = self
        
        class mockMessagingUtils:
            def send_cancel(self, run):
                parent.cancelledRun = run
        
        return mockMessagingUtils
        
    
    def test_cancel_queued(self):
        reductionRun = self.createReductionRun()
    
        with patch('reduction_variables.utils.MessagingUtils', self.createMockMessagingUtils()):
            ReductionRunUtils().cancelRun(reductionRun)
            self.assertEqual(self.cancelledRun, reductionRun, "Expected that the run to be cancelled was this one")
            self.assertEqual(reductionRun.status, StatusUtils().get_error(), "Expected the run to have error status, was %s " % reductionRun.status.value)
    
    
    def test_cancel_rerun_queued(self):
        reductionRun = self.createReductionRun()
        reductionRun.status = StatusUtils().get_error()
        retryRun = self.createReductionRun()
        reductionRun.retry_run = retryRun
        
        with patch('reduction_variables.utils.MessagingUtils', self.createMockMessagingUtils()):
            ReductionRunUtils().cancelRun(reductionRun)
            self.assertEqual(self.cancelledRun, retryRun, "Expected that the run to be cancelled was this one")
            self.assertEqual(retryRun.status, StatusUtils().get_error(), "Expected the run to have Error status, was %s " % retryRun.status.value)
    
    
    def test_cancel_not_queued(self):
        # should not cancel a run that's not queued 
        statusList = [ "get_error"
                     , "get_completed"
                     , "get_processing"
                     , "get_skipped"
                     ]
                     
        for statusMember in statusList:
            status = getattr(StatusUtils(), statusMember)()
            reductionRun = self.createReductionRun()
            reductionRun.status = status
            
            with patch('reduction_variables.utils.MessagingUtils', self.createMockMessagingUtils()):
                ReductionRunUtils().cancelRun(reductionRun)
                self.assertEqual(self.cancelledRun, None, "Expected that no run was cancelled when trying %s" % statusMember)
                self.assertEqual(reductionRun.status, status, "Expected the run to have %s status, was %s" % (status.value, reductionRun.status.value))
    
    
    def test_createRetryRun(self):    
        reductionRun = self.createReductionRun()
        retryRun = ReductionRunUtils().createRetryRun(reductionRun)
        
        self.assertEqual(reductionRun.retry_run, retryRun, "Expected reductionRun.retry_run to be updated to retryRun")
        
        shouldBeEqualFields = [ "instrument"
                              , "experiment"
                              , "run_number"
                              ]
        for field in shouldBeEqualFields:
            self.assertEqual(getattr(reductionRun, field), getattr(retryRun, field), "Expected field %s to be equal" % field)
        
        self.assertEqual(reductionRun.run_version+1, retryRun.run_version, "Expected run version to be incremented, was %i vs %i" % (reductionRun.run_version, retryRun.run_version))
        
        self.assertEqual(reductionRun.script, retryRun.script, "Expected variable scripts to be the same, but were %s... and %s..." % (reductionRun.script[:50], retryRun.script[:50]))
        
        self.assertEqual(set(reductionRun.data_location.all()), set(retryRun.data_location.all()), "Expected data locations to be the same")
    
    
    def test_createRetryRun_duplicate(self):
        reductionRun = self.createReductionRun()
        retryRun1 = ReductionRunUtils().createRetryRun(reductionRun)
        retryRun2 = ReductionRunUtils().createRetryRun(reductionRun)
        
        self.assertEqual(retryRun1.run_version+1, retryRun2.run_version, "Expected run version to be correctly incremented, was %i vs %i" % (retryRun1.run_version, retryRun2.run_version))
        
        
    def test_get_script_and_arguments_successful(self):
        run_variables = []

        reduction_run = getReductionRun()
        reduction_run.script = getValidScript("reduce.py")
        
        variable = RunVariable(reduction_run=reduction_run,name='test',value='testvalue1',type='text',is_advanced=False)
        variable.save()
        run_variables.append(variable)
        variable = RunVariable(reduction_run=reduction_run,name='advanced_test',value='testvalue2',type='text',is_advanced=True)
        variable.save()
        run_variables.append(variable)

        script, arguments = ReductionRunUtils().get_script_and_arguments(reduction_run)

        self.assertNotEqual(script, None, "Expecting to get a script path back.")
        self.assertNotEqual(script, "", "Expecting to get a script path back.")
        self.assertNotEqual(arguments, None, "Expecting to get some arguments path back.")
        self.assertNotEqual(arguments, {}, "Expecting to get some arguments path back.")
        self.assertTrue('standard_vars' in arguments, "Expecting arguments to have a 'standard_vars' key.")
        self.assertTrue('advanced_vars' in arguments, "Expecting arguments to have a 'advanced_vars' key.")
        self.assertEqual(arguments['standard_vars']['test'], 'testvalue1', "Expecting to find testvalue1 in standard_vars.")
        self.assertEqual(arguments['advanced_vars']['advanced_test'], 'testvalue2', "Expecting to find testvalue2 in advanced_vars.")
        
