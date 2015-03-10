# Autoreduction Worker Technical Documentation

## Overview
This is technical documentation for the pyhton scripts, which are installed with the ISIS post process rpm, 
and which subscribes and listen to ActiveMQ for messages to execute instrument reduction scripts.

## [queueProcessor.py](https://github.com/mantidproject/autoreduce/blob/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/usr/bin/queueProcessor.py)
This script subscribes 'python PostProcessAdmin.py destination data' (as a subprocess) to the ActiveMQ queue(s) specific by 'amq_queues' in the config file [post_process_consumer.conf](https://github.com/mantidproject/autoreduce/blob/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/etc/autoreduce/post_process_consumer.conf),
where 'destination' is the name of the queue, 'data' is the data message received by the queue and 'PostProcessAdmin.py' 
is the script which adminstrates the processing instructions from the message.

## [PostProcessAdmin.py](https://github.com/mantidproject/autoreduce/blob/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/usr/bin/PostProcessAdmin.py)
PostProcessAdmin.py processes messages from '/queue/ReductionPending'. The main method reduce() of PostProcessAdmin
gets called if initial inspections of the message passes. reduce() starts by sending a message to the
reduction_started queue to tell that reduction has started. Then sets up the specific reduction script, reduce.py,
for execution in a number of steps, where the path to this script is provided in the data message key 'reduction_script'. 

reduce.py imports reduce_vars.py as web_var. reduce_vars.py contains the default values of the standard and advanced
variables that can be adjusted in the [autoreduction WebApp](https://github.com/mantidproject/autoreduce/tree/master/WebApp/ISIS).

In reduce() reduce.py is loaded and initialised. Default web_var variables are then substituted by those provided in the
data message key 'reduction_arguments', before executing the reduce.py method: 'out_directories = main(input_file,output_directory)', 
where the arguments of main() 'input_file' is the data file and 'output_directory' is the temporary 
directory to save the processed files to. If main() returns output directories in 'out_directories' then the temporary
reduced data are first copied to this folder before copying the reduce data to a archieve location. 

If reduction goes well then a message to 'reduction_complete' is send with appended information about where the
reduced data was copied to. And if error occur then a message to 'reduction_error' is send with information about
the error.
