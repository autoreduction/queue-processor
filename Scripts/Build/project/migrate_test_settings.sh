#!/usr/bin/env sh
# Simple shell script to move test_settings.py to settings.py
cp Scripts/ActiveMQTests/test_settings.py Scripts/ActiveMQTests/settings.py
cp utils/test_settings.py utils/settings.py
cp WebApp/autoreduce_webapp/autoreduce_webapp/test_settings.py WebApp/autoreduce_webapp/autoreduce_webapp/settings.py
cp QueueProcessors/AutoreductionProcessor/test_settings.py QueueProcessors/AutoreductionProcessor/settings.py
cp QueueProcessors/QueueProcessor/test_settings.py QueueProcessors/QueueProcessor/settings.py
