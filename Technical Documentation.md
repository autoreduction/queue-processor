# Autoreduction Worker Technical Documentation

## Overview
This is technical documentation for the Python scripts, which are installed with the ISIS post process RPM, 
and which subscribe and listen to ActiveMQ for messages to execute instrument reduction scripts.

## [queueProcessor_daemon.py](https://github.com/mantidproject/autoreduce/blob/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/usr/bin/queueProcessor_daemon.py)
This runs queueProcessor.py as a daemon service, e.g., `python /usr/bin/queueProcessor_daemon.py start` will start the service.

## [queueProcessor.py](https://github.com/mantidproject/autoreduce/blob/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/usr/bin/queueProcessor.py)
This script subscribes to the ActiveMQ queue(s) specific by 'amq_queues' in the config file [post_process_consumer.conf](https://github.com/mantidproject/autoreduce/blob/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/etc/autoreduce/post_process_consumer.conf), most likely `/queue/ReductionPending`.
Upon receiving a message indicating that a run is pending for reduction, in `on_message()` it will queue the job for as long as there is no other run with the same RB number occurring - `shouldProceed()` - and then calls PostProcessAdmin.py with the message to be reduced.
It also processes cancellation messages, in case a run that's scheduled should be cancelled before the message arrives.



## [PostProcessAdmin.py](https://github.com/mantidproject/autoreduce/blob/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/usr/bin/PostProcessAdmin.py)
PostProcessAdmin.py processes the reduction runs. The main method `reduce()` of PostProcessAdmin
gets called if initial inspections of the message passes. `reduce()` starts by sending a message to the
reduction_started queue to tell that reduction has started. It then sets up the various output directories, for temporary output, logging, and the eventual final output, and ensures that it has the correct access to them. 
It then sets up the specific reduction script, reduce.py, for execution, where the script is provided in the data message key 'reduction_script'. 

reduce.py may import reduce_vars.py as web_var. reduce_vars.py contains the default values of the standard and advanced
variables that can be adjusted in the [autoreduction WebApp](https://github.com/mantidproject/autoreduce/tree/master/WebApp/ISIS). It's expected that if reduce.py imports reduce_vars.py, it provides a path to that file (e.g. `sys.path..append("/isis/NDXGEM/user/scripts/autoreduction")`).

In `reduce()` reduce.py is loaded and initialised: 

    reduce_script = imp.new_module('reducescript')
    exec self.reduction_script in reduce_script.__dict__ # loads the string as a module into reduce_script
    
Default web_var variables are then substituted by those provided in the
data message key 'reduction_arguments', before executing the reduce.py script: 

    out_directories = reduce_script.main(input_file=str(self.data_file), output_dir=str(reduce_result_dir))
     
For the arguments of `main()`, `'input_file'` is the data file and `'output_directory'` is the temporary 
directory to save the processed files to. If main() returns output directories in 'out_directories' then the temporary
reduced data are first copied to this folder before copying the reduce data to an archive location. 

Finally, if reduction goes well then a message to 'reduction_complete' is send with appended information about where the
reduced data was copied to. If error occur then a message to 'reduction_error' is send with information about
the error. In some cases, `'retry_in'` will be set in the message data, which indicates that the run is to be retried
in that many seconds' time.
