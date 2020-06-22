# utils

Contains all the common and shared code for the project.
This is mainly with a view to reduce duplication for common functionality such as logging, 
accessing external services such as the database and the message queues.

## To Setup Locally

- Copy `build/ansible-compute/roles/queue_processors/templates/utils_settings.py.j2`
  to `utils/settings.py`
 - Modify `utils/settings.py` as required