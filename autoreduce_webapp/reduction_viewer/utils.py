import logging, os, sys, time, datetime
sys.path.append(os.path.join("../", os.path.dirname(os.path.dirname(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "autoreduce_webapp.settings"
logger = logging.getLogger('app')
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
        """
        Try to cancel the run given, or the run that was scheduled as the next retry of the run. When we cancel, we send a message to the backend queue processor, telling it to ignore this run if it arrives (most likely through a delayed message through ActiveMQ's scheduler). We also set statuses and error messages. If we can't do any of the above, we set the variable (retry_run.cancel) that tells the frontend to not schedule another retry if the next run fails.
        """
        from reduction_variables.utils import MessagingUtils
        
        def setCancelled(run):
            run.message = "Run cancelled by user"
            run.status = StatusUtils().get_error()
            run.finished = timezone.now().replace(microsecond=0)
            run.retry_when = None
            run.save()
        
        if reductionRun.status == StatusUtils().get_queued(): # this is the queued run, send the message to queueProcessor to cancel it
            MessagingUtils().send_cancel(reductionRun)
            setCancelled(reductionRun)
            
        # otherwise this run has already failed, and we're looking at a scheduled rerun of it
        elif not reductionRun.retry_run: # we don't actually have a rerun, so just ensure the retry time is set to "Never" (None)
            reductionRun.retry_when = None
        
        elif reductionRun.retry_run.status == StatusUtils().get_queued(): # this run is being queued to retry, so send the message to queueProcessor to cancel it, and set it as cancelled
            MessagingUtils().send_cancel(reductionRun.retry_run)
            setCancelled(reductionRun.retry_run)
        
        elif reductionRun.retry_run.status == StatusUtils().get_processing(): # we have a run that's retrying, so just make sure it doesn't retry next time
            reductionRun.cancel = True
            reductionRun.retry_run.cancel = True
            
        else: # the retry run already completed, so do nothing
            pass
            
        # save the run states we modified
        reductionRun.save()
        if reductionRun.retry_run:
            reductionRun.retry_run.save()
            

    def createRetryRun(self, reductionRun, overwrite=None, script=None, variables=None, delay=0, username=None, description=''):
        """
        Create a run ready for re-running based on the run provided. 
        If variables (RunVariable) are provided, copy them and associate them with the new one, otherwise use the previous run's.
        If a script (as a string) is supplied then use it, otherwise use the previous run's.
        """
        from reduction_variables.utils import InstrumentVariablesUtils, VariableUtils
        
        run_last_updated = reductionRun.last_updated
        
        if username == 'super':
            username = 1

        # find the previous run version, so we don't create a duplicate
        last_version = -1
        for run in ReductionRun.objects.filter(experiment=reductionRun.experiment, run_number=reductionRun.run_number):
            last_version = max(last_version, run.run_version)
        
        try:
            # get the script to use:
            script_text = script if script is not None else reductionRun.script
        
            # create the run object and save it
            new_job = ReductionRun( instrument = reductionRun.instrument
                                  , run_number = reductionRun.run_number
                                  , run_name = description
                                  , run_version = last_version+1
                                  , experiment = reductionRun.experiment
                                  , started_by = username
                                  , status = StatusUtils().get_queued()
                                  , script = script_text
                                  , overwrite = overwrite
                                  )
            new_job.save()
            
            reductionRun.retry_run = new_job
            reductionRun.retry_when = timezone.now().replace(microsecond=0) + datetime.timedelta(seconds=delay if delay else 0)
            reductionRun.save()
            
            ReductionRun.objects.filter(id = reductionRun.id).update(last_updated = run_last_updated)
            
            # copy the previous data locations
            for data_location in reductionRun.data_location.all():
                new_data_location = DataLocation(file_path=data_location.file_path, reduction_run=new_job)
                new_data_location.save()
                new_job.data_location.add(new_data_location)
                
            if variables is not None:
                # associate the variables with the new run
                for var in variables:
                    var.reduction_run = new_job
                    var.save()
            else:
                # provide variables if they aren't already
                InstrumentVariablesUtils().create_variables_for_run(new_job)

            return new_job
            
        except Exception as e:
            logger.error(e.message)
            new_job.delete()
            raise
            
            
    def get_script_and_arguments(self, reductionRun):
        """
        Fetch the reduction script from the given run and return it as a string, along with a dictionary of arguments.
        """
        from reduction_variables.utils import VariableUtils
        
        script = reductionRun.script

        run_variables = RunVariable.objects.filter(reduction_run=reductionRun)
        standard_vars, advanced_vars = {}, {}
        for variables in run_variables:
            value = VariableUtils().convert_variable_to_type(variables.value, variables.type)
            if variables.is_advanced:
                advanced_vars[variables.name] = value
            else:
                standard_vars[variables.name] = value

        arguments = { 'standard_vars' : standard_vars, 'advanced_vars': advanced_vars }

        return (script, arguments)
        
        
class ScriptUtils(object):
    def get_reduce_scripts(self, scripts):
        """
        Returns a tuple of (reduction script, reduction vars script), each one a string of the contents of the script, given a list of script objects. 
        """
        script_out = None
        script_vars_out = None
        for script in scripts:
            if script.file_name == "reduce.py":
                script_out = script
            elif script.file_name == "reduce_vars.py":
                script_vars_out = script
        return script_out, script_vars_out

    def get_cache_scripts_modified(self, scripts):
        """
        Returns the last time the scripts in the database were modified (in seconds since epoch).
        """
        script_modified = None
        script_vars_modified = None

        for script in scripts:
            if script.file_name == "reduce.py":
                script_modified = self._convert_time_from_string(str(script.created))
            elif script.file_name == "reduce_vars.py":
                script_vars_modified = self._convert_time_from_string(str(script.created))
        return script_modified, script_vars_modified

    def _convert_time_from_string(self, string_time):
        time_format = "%Y-%m-%d %H:%M:%S"
        string_time = string_time[:string_time.find('+')]
        return int(time.mktime(time.strptime(string_time, time_format)))
