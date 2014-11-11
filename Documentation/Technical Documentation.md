# Autoreduction Web App Technical Documentation

## Overview


## Contents

1. [Overview](#overview)
2. [Technologies](#technologies)
    1. [Django](#-django-https-www-djangoproject-com-)
    2. [ActiveMQ](#-activemq-http-activemq-apache-org-)
    3. [Stomp.py](#-stomp-py-https-github-com-jasonrbriggs-stomp-py-)
    4. [MySQL](#-mysql-http-www-mysql-com-)
    5. [JavaScript](#javascript)
    6. [CSS](#css)
3. [Components](#components)
    1. [autoreduce_webapp](#)
    2. [reduction_viewer](#reduction_viewer)
    3. [reduction_variables](#reduction_variables)
4. [Templates](#templates)
3. [Tests](#test#)
4. [Areas for Improvement](#areas-for-improvement)
5. [Possible Problems & Solutions](#possible-problems-&-solutions)

## Technologies

### [Django](https://www.djangoproject.com/)
**Version:** 1.7

Web framework for python. Abstracts away various tasks such as database access, logging, admin interface, templating and URL routing. The web server proxies request through to Django (via wsgi with Apache or fcgi with IIS) that then handles loading the correct files, managing errors, etc.

**Updating:** Django is installed through `pip` or `easy_install`. Update using these tools for best results. Make sure to check https://docs.djangoproject.com/en/1.7/releases/ for any breaking changes before updating.

### [ActiveMQ](http://activemq.apache.org/) 
**Version:** 5.10.0

ActiveMQ is a messaging server that supports publish/subscribe to both queues and topics. It handles multiple protocols but only Stomp is being used in this web app. It should be ensured that the server is restricted to SSL and with credentials (See installation instructions).

### [Stomp.py](https://github.com/jasonrbriggs/stomp.py)
**Version:** 4.0.12

Stomp.py is a python client for communicating with messaging servers using the Stomp protocol.

### [MySQL](http://www.mysql.com/)
**Version:** 5.6.21

Database to store all information about the web app (users, reduction runs, notifications).

### JavaScript
**Third Party Libraries:**
* [JQuery](http://jquery.com/) - Utility library to make DOM manipulation, event handling, etc. easier and more cross-browser compatible.
* [Bootstrap v3.3.0](http://getbootstrap.com/) - Layout interaction and components (such as dropdown menus, modal windows, etc.)
* [Bootstrap-Switch](http://www.bootstrap-switch.org/) - Provides a toggle script for the instrument variables page.
* [FastDOM](https://github.com/wilsonpage/fastdom) - Allows for better handling of multiple DOM manipulations. Prevents [layout thrashing](http://wilsonpage.co.uk/preventing-layout-thrashing/).
* [Prettify](https://code.google.com/p/google-code-prettify/) - Provides syntax highlighting for the script preview window.

**Notes:** 
* **polyfills.js** - This file provides some often used features that are missing from some browsers. These include functions such as `startsWith` and `endsWith` for strings.
* **cookies.js** - Easier saving and reading of cookies taken from https://developer.mozilla.org/en-US/docs/Web/API/document.cookie.
* All other JavaScript files have their code wrapped in a [IIFE](http://benalman.com/news/2010/11/immediately-invoked-function-expression/) (Immediately-Invoked Function Expression) to prevent polluting the global scope with variables that could possibly conflict. All have a single `init()` function that is called on page load, this function handles any initialisation that is needed, such as hooking up event handlers.

### CSS
**Third Party Libraries:**
* [Bootstrap](http://getbootstrap.com/) - Layout interaction and components (such as dropdown menus, modal windows, etc.) and provide a grid layout to make responsive layout much easier.
* [Prettify](https://code.google.com/p/google-code-prettify/) - Provides syntax highlighting for the script preview window.
* [Font Awesome](http://fortawesome.github.io/Font-Awesome/) - Icon Font used for the icons on the sight to make them scalable and clear on all displays.

## Components

The web application is split into 3 components, known as apps in Django. These are:
* autoreduce_webapp
* reduction_viewer
* reduction_variables

### autoreduce_webapp
This is the core of the web app. It handles the application-wide settings, utilities and shared services.

#### queue_processor.py
The `queue_processor.py` isn't strictly part of the web application but runs separately as a service but makes use of the modules made available by autoreduce_webapp (such as models and utilities). This contains a Stomp Client and Listener that sits and listens for messages from ActiveMQ on the following queues:
* `/queue/DataReady`
* `/queue/ReductionStarted`
* `/queue/ReductionComplete`
* `/queue/ReductionError`

When it retrieves a message from one of these queues it inspects the message (a [JSON](http://www.json.org/) object) and, depending on the queue the message was from, updates the database with the details it finds.

This actions this script takes are:
* `DataReady` - Create a new ReductionRun record representing the data that has come off the instrument. This then sends a message to the `/queue/ReductionPending` queue for it to be picked up by the autoreduction service.
* `ReductionStarted` - This simply updated the status of the saved ReductionRun to note that the reduction job is now being performed by the autoreduction service.
* `ReductionComplete` - This updates the status and performs post-processing. ICAT is updated with the reduction details. The reduced data is checked for .png files and these converted to a [base64](http://css-tricks.com/data-uris/) encoded string and saved in the database to be shown via the web application.
* `ReductionError` - This logs the error that was retrieved and updated the status of the ReductionRun.

#### icat_communication.py

This handles all communication to [ICAT](http://icatproject.org/) and acts as a wrapper to the icat python client. 

This is used in two ways. 

The first uses the credentials store in the `settings.py` file of autoreduce_webapp. This user should have elevated permissions and so this method is used for activities such as getting all upcoming experiments for an instrument and running the tests.
```python
with ICATCommunication() as icat_client:
    # icat_client.do_something()
```
The second passes in the current users session ID. This should be used for most calls as it will correctly filter results based on the permission of the user and on what they are associated with.
```python
with ICATCommunication(AUTH='uows',SESSION={'sessionid':request.session.get('sessionid')}) as icat:
    # icat_client.do_something()
```

ICATCommunication also supports more overrides passed in as kwargs but aren't currently used outside of tests. 

```python
ICATCommunication(URL='',AUTH='',SESSION={},USER='',PASSWORD='')
```

ICATCommunication will logout of ICAT when it goes out of the scope of the `with` statement.

#### uows_client.py

This handles communication with the User Office Web Service to handle authentication and retrieving user details.

It provides 3 method: `check_session`, `get_person` and `logout`, all which take in the users current session ID. 

`get_person` returns a trimmed-down version of the details stored in the User Office system. (first name, last name, email and usernumber)

The UOWSClient can be called with an optional kwarg parameter that sets the URL of the web service which defaults to what is stored in the `settings.py` of autoreduce_webapp.

```python
with UOWSClient(URL='') as uows_client:
    # uows_client.do_something()
```

#### backends.py

This contains custom backend functions. Backends are things such as authentication and database access.

Currently there is a single custom backend, `UOWSAuthenticationBackend`, that provides authentication via the User Office system.

UOWSAuthenticationBackend provides a `authenticate` function that takes in a session ID and verifies it's valid using uows_client.py. If valid it then checks if an associated user account exists in the local MySQL database, creating one if none is found. This function also calls ICAT to update the users permission status (whether they are staff or superuser/admin) 

#### utils.py

Provides application-wide utilities. Contains `SeparatedValuesField` that can be used by models to implement a list/array-like field property. Values are stored in the database as text separated by the pipe character (|). This is currently only used by ReductionRun to store graphs.

#### view_utils.py

Provides application-wide function decorators for view methods. These include things like checking a session ID is still valid (`login_and_uows_valid`) or that a user is a staff memeber (`require_staff`). `require_staff` and `require_admin` will both throw a [403 Forbidden](http://en.wikipedia.org/wiki/HTTP_403) is the current user doesn't have the appropriate permissions. If not logged in, the user will be redirected to the login page first.

The main function worth taking note of is `render_with`. This is used by all view functions except those that are called from within another view (as these don't trigger function decorators). When used, this expect the function to return a dictionary (the context dictionary that will be used by the template) which it then adds any active notifications, flags and values such as support email and then calling the `render_to_response` on the appropriate template file with the dictionary fully populated. This means there is a single location to put all context variables that are needed on all (or most) pages without having to add it to each view function.

Example:
```python
@render_with('template_name.html')
```

#### templatetags

The templatetags directory contains custom filters and tags that can be used within templates. These need to be loaded in the same was as built in [Django tags/filters](https://docs.djangoproject.com/en/1.7/ref/templates/builtins/):
```
{% load colour_table_rows %}
```

* **colour_table_rows.py** - Takes in the status of a ReductionRun and returns back the appropriate Bootstrap colour class.
* **get_user_name.py** - Takes in a usernumber and returns back a mailto link with the users full name.
* **natural_time_difference.py** - Takes in a start and end datetime and returns back a duration in days, hours, minutes and seconds where appropriate.
* **replace.py** - Replaces all occurrences of a string with another in the given text.
* **variable_type.py** - Used by the edit variables forms to return the correct input type for values such as "list_number" or "boolean".
* **view.py** - Provides the ability to include a view function from within a template. Note: This doesn't trigger any middleware/function decorators on the view function.


### reduction_viewer

This contains most of the models and logic for the web app itself. Everything not related to run/instrument variables are found within this app. 

#### models.py

Models are the instances of database records. Each model matches against a table in the database.

* **Instrument** - A simple model containing the instrument name and whether it is active in the web app.
* **Experiment** - A record containing only the experiment reference number, used to link reduction runs together.
* **Status** - Status of the reduction run, either Queued, Processing, Completed or Error.
* **ReductionRun** - The main model that contains most information about a reduction run job. Run_version will begin at 0 for an initial reduction triggered when coming off the instrument. This is important as it is used to indicate in the UI that the job was started by "Autoreduction Service" 
* **DataLocation** - Stores the file path of the data for a reduction run.
* **ReductionLocation** - Stored the output directories of a completed reduction job.
* **Setting** - Key/Value pair of settings to be used throughout the web app and can be quickly and easily changed through the admin interface. Current settings are: `support_email`, `admin_email` and `ICAT_YEARS_TO_SHOW`.
* **Notification** - A model for showing notifications at the top of pages. These have various severities (info, warning and error) that determine the colour of the notification. It is possible to limit notifications to only be shown to staff using the `is_staff_only` boolean and notifications can be enabled/disabled by setting the `is_active` boolean. Some notifications are created and shown on-the-fly in the `view_utils.py` 

#### utils.py

### reduction_variables

All models and logic related to run/instrument variables are found within this app.

#### models.py

#### utils.py

## Templates

## Tests

All tests are run using `manage.py test` from the root of the web application. Please see: https://docs.djangoproject.com/en/1.7/topics/testing/ for more info.

Tests are split across 3 files (tests.py in each application) and these have sub-classes that split the tests up into testing different utilities (such as the queue processor). All test method names must begin with test.

```
python manage.py test autoreduce_webapp.tests.QueueProcessorTestCase
```
```
python manage.py test autoreduce_webapp.tests.ICATCommunicationTestCase
```
```
python manage.py test autoreduce_webapp.tests.UOWSClientTestCase
```
```
python manage.py test reduction_variables.tests.InstrumentVariablesUtilsTestCase
```
```
python manage.py test reduction_variables.tests.VariableUtilsTestCase
```
```
python manage.py test reduction_variables.tests.ReductionVariablesUtilsTestCase
```
```
python manage.py test reduction_variables.tests.MessagingUtilsTestCase
```

Note: UOWSClientTestCase requires you enter a valid username and password for the User Office Web Service.

## Areas for Improvement

### Caching
**Ticket:** [#10252](http://trac.mantidproject.org/mantid/ticket/10252)
Depending on usage, a cache may be needed to sit between the web app and the ICAT server to prevent repeat calls for the same information. During testing this hadn't yet shown to be an issue but having multiple users may require it. 

### Reduced Data Size
**Ticket:** [#10459](http://trac.mantidproject.org/mantid/ticket/10459)
It would be nice to display how much disk space reduced files are taking up at the run, experiment and instrument level.

### Refactor DataLocation and ReductionLocation
DataLocation and ReductionLocation could be reduced into a single Location model with a 'type' property to specify which a path relates to. These were implemented as two models as it was easy to call `reduction_run.data_location.all()` to get data location. I have since learned you should be able to call `filter()` on the relation, E.g. `reduction_run.location.filter(type='data')`

## Possible Problems & Solutions

