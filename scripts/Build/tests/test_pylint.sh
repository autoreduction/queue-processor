#!/usr/bin/env sh
# Run pylint without check for C0103 (invalid-name) as this triggers on module names
# There is currently no work around for this - we should change module names to lower case

SUCCESS=0
FILES="monitors
       scripts/ActiveMQTests/send_message.py
       scripts/ActiveMQTests/test_stomp_activemq.py
       scripts/manual_submission_script
       scripts/NagiosChecks/autoreduce_checklastrun.py
       WebApp/autoreduce_webapp/autoreduce_webapp/
       QueueProcessors/AutoreductionProcessor"

for file in $FILES
do
    RESULT="$(pylint -d C0103 $file)"
    retVal=$?
    if [ $retVal -ne 0 ]; then
        echo "$RESULT"
        SUCCESS=1
    fi
done


# Should be able to improve the below when we fix W0141,R0401

RESULT="$(pylint -d C0103,W0141,R0401 QueueProcessors/QueueProcessor)"
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "$RESULT"
    SUCCESS=1
fi

if [ $SUCCESS -ne 0 ]; then
    exit 1
else
    exit 0
fi
