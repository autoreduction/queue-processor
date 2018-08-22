This template file is used to instruct Apache of where the content to serve is located.
In order to get this up and running with Apache you must do the following:

* Rename ``apache_django_wsgi.conf.template`` to ``apache_django_wsgi.conf``
* Update the file paths in ``apache_django_wsgi.conf`` to the correct directories
* Locate ``httpd.conf`` (this will be included in the Apache install on the system)
* Add the line ``Include /path/to/git/repo/WebApp/autoreduce_webapp/apache/apache_django_wsgi.conf``to ``httpd.conf``
* Restart the Apache service on the machine
