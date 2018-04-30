#!/usr/bin/env sh
# Run pylint without check for C0103 (invalid-name) as this triggers on module names
# There is currently no work around for this - we should change module names to lower case

pylint -d C0103 EndOfRunMonitor

pylint -d C0103 Scripts/ActiveMQTests/send_message.py
pylint -d C0103 Scripts/ActiveMQTests/test_stomp_activemq.py
pylint -d C0103 Scripts/ManualSubmissionScript
pylint -d C0103 Scripts/NagiosChecks/autoreduce_checklastrun.py

pylint -d C0103,W0403,W0141,R0401,C0413 QueueProcessors/QueueProcessor
pylint -d C0103,W0403 QueueProcessors/AutoreductionProcessor
pylint -d C0103 WebApp/autoreduce_webapp/autoreduce_webapp/