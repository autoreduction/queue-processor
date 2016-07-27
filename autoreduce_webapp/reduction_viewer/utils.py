import logging, os, sys, datetime
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
logger = logging.getLogger(__name__)
from django.utils import timezone
from reduction_viewer.models import Instrument, Status, ReductionRun, DataLocation
from reduction_variables.models import RunVariable

class StatusUtils(object):
    def _get_status(self, status_value):
        """
        Helper method that will try to get a status matching the given name or create one if it doesn't yet exist
        """
        status, created = Status.objects.get_or_create(value=status_value)
        if created:
            logger.warn("%s status was not found, created it." % status_value)
        return status

    def get_error(self):
        return self._get_status("Error")

    def get_completed(self):
        return self._get_status("Completed")

    def get_processing(self):
        return self._get_status("Processing")

    def get_queued(self):
        return self._get_status("Queued")

    def get_skipped(self):
        return self._get_status("Skipped")
            
class InstrumentUtils(object):
    def get_instrument(self, instrument_name):
        """
        Helper method that will try to get an instrument matching the given name or create one if it doesn't yet exist
        """
        instrument, created = Instrument.objects.get_or_create(name__iexact=instrument_name)
        if created:
            instrument.name = instrument_name
            instrument.save()
            logger.warn("%s instrument was not found, created it." % instrument_name)
        return instrument
        
class ReductionRunUtils(object):

    def cancelRun(self, reductionRun):
        from reduction_variables.utils import MessagingUtils
        
        if reductionRun.status == StatusUtils().get_queued(): # this is the queued run, send the message to queueProcessor to cancel it
            MessagingUtils().send_cancel(reductionRun)
            
        # otherwise this run has already failed, and we're looking at a scheduled rerun of it
        elif not reductionRun.retry_run: # we don't actually have a rerun, so just ensure the retry time is set to "Never" (None)
            reductionRun.retry_when = None
        
        elif reductionRun.retry_run.status == StatusUtils().get_queued(): # this run is being queued to retry, so send the message to queueProcessor to cancel it, and set it as cancelled
            MessagingUtils().send_cancel(reductionRun.retry_run)
            reductionRun.retry_run.message = "Run cancelled by user"
            reductionRun.retry_run.status = StatusUtils().get_error()
            reductionRun.retry_run.finished = timezone.now().replace(microsecond=0)
            reductionRun.retry_run.retry_when = None
        
        elif reductionRun.retry_run.status == StatusUtils().get_processing(): # we have a run that's retrying, so just make sure it doesn't retry next time
            reductionRun.cancel = True
            reductionRun.retry_run.cancel = True
            
        else: # the retry run already completed, so do nothing
            pass
            
        # save the run states we modified
        reductionRun.save()
        if reductionRun.retry_run:
            reductionRun.retry_run.save()
            

    def createRetryRun(self, reductionRun, scripts=None, variables=None, delay=0):
        """
        Create a run ready for re-running based on the run provided. If variables are provided, copy them and associate them with the new one, otherwise generate variables based on the previous run. If ScriptFile objects are supplied, use them, otherwise use the previous run's.
        """
        from reduction_variables.utils import InstrumentVariablesUtils
        
        # find the previous run version, so we don't create a duplicate
        last_version = -1
        for run in ReductionRun.objects.filter(experiment=reductionRun.experiment, run_number=reductionRun.run_number):
            last_version = max(last_version, run.run_version)
            
        try:
            # create the run object and save it
            new_job = ReductionRun(
                instrument = reductionRun.instrument,
                run_number = reductionRun.run_number,
                run_name = "",
                run_version = last_version+1,
                experiment = reductionRun.experiment,
                #started_by=request.user.username, # commented out for the test server only
                status = StatusUtils().get_queued()
                )
            new_job.save()
            
            reductionRun.retry_run = new_job
            reductionRun.retry_when = timezone.now().replace(microsecond=0) + datetime.timedelta(seconds=delay if delay else 0)
            reductionRun.save()
            
            # copy the previous data locations
            for data_location in reductionRun.data_location.all():
                new_data_location = DataLocation(file_path=data_location.file_path, reduction_run=new_job)
                new_data_location.save()
                new_job.data_location.add(new_data_location)
                
            if not variables: # provide variables if they aren't already
                variables = InstrumentVariablesUtils().get_variables_for_run(new_job)
            for var in variables:
                new_var = RunVariable(name=var.name, value=var.value, type=var.type, is_advanced=var.is_advanced, help_text=var.help_text) # copy variable
                new_var.reduction_run = new_job # associate it with the new run
                new_job.run_variables.add(new_var)
                
                # add scripts based on whether some were supplied
                if not scripts:
                    scripts = var.scripts.all()
                for script in scripts:
                    new_var.scripts.add(script)
                    
                new_var.save()
                    
            return new_job
            
        except:
            new_job.delete()
            raise