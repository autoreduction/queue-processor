# Apache Server on Windows setup

One alternative to using IIS on Windows is to use Apache to host the front end of the autoreduction service. 

## Prerequisites

If you have already installed Python then you MUST have the 32 bit version. You version of Windows does not matter but all of the components in this guide must be the 32 bit versions to result in a working system. If you haven't already installed Python then this will be covered in the next section. 

You will also need a program such as WinRar which can unzip tar.gz files.

## Installing necessary components

Firstly, you will need to download and install the different elements that will make up the Apache server. To do this, follow the instructions as follows:

1. Download Apache 2.2 [here](https://archive.apache.org/dist/httpd/binaries/win32/httpd-2.2.25-win32-x86-openssl-0.9.8y.msi). The download will contain an MSI file which you should then run to install the Apache server. The default installation options should be correct but make sure you check the details as you click through. One potential cause for error will be selecting the port that the server should run on. By default, Apache will try to select port 80, but this could already be being used by IIS. In which case, select a different port to use (another commonly chosen port is 8080).

2. If you have not already done so, you will need to download Python 2.7 32 Bit. Click [here](https://www.python.org/ftp/python/2.7.13/python-2.7.13.msi) for 2.7.13 (there may be newer versions available at the time of reading). The installer should guide you through the process in detail.

3. You will also need to download MySQL. I suggest downloading the Community Edition such that you can control the installation through MySQL Installer which is easy to use and yields the best results. You can download MySQL 5.7.17 [here](https://cdn.mysql.com//Downloads/MySQLInstaller/mysql-installer-community-5.7.17.0.msi) (Again, there could be newer versions available). When running the installer, choose the 'custom' option for installation. On the product selection screen, you need to select the following three components: MySQL Server(x86), MySQL Workbench(x86), Connector/Python(2.7)(x86). Once you have all three of them selected, install the products and finish the installation. Make sure to make a note of the root password for your MySQL server. In order for MySQL Workbench to run correctly, you will also need to install a C++ distribution which you can find [here](https://download.microsoft.com/download/2/E/6/2E61CFA4-993B-4DD4-91DA-3737CD5CD6E3/vcredist_x86.exe).

4. Next, you need to load MySQL Workbench, connect to the local database and create a new schema called 'autoreduction'. 

5. In order for Python and MySQL to talk to eachother properly, you will also need MySQLdb which can be found [here](https://kent.dl.sourceforge.net/project/mysql-python/mysql-python/1.2.3/MySQL-python-1.2.3.win32-py2.7.msi) The installer should automatically discover your existing Python installation and place the package in the correct place.

6. You will then need to download the py27 wsgi module for Apache so that Apache knows how to correctly serve up the Django autoreduction application. You can find the wsgi module [here](https://github-cloud.s3.amazonaws.com/releases/15648929/da6a22d0-08a6-11e5-8a5b-0d214c853629.gz?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAISTNZFOVBIJMK3TQ%2F20170221%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20170221T091852Z&X-Amz-Expires=300&X-Amz-Signature=77c12c80d7f48ccdc465184880a0f424afcc097c57cd7b8054ae4306ba1d057e&X-Amz-SignedHeaders=host&actor_id=0&response-content-disposition=attachment%3B%20filename%3Dmod_wsgi-windows-4.4.12.tar.gz&response-content-type=application%2Foctet-stream). You will then need to unzip the tar.gz file. Inside the file, you will find four folders and you need to choose Apache22-Win32. Further inside that folder, you will find the mod_wsgi-py27-VC9 file that you then need to extract to the following location: C:\Program Files (x86)\Apache Software Foundation\Apache2.2\modules

It will also be worth testing your setup at this point to ensure that Apache is working at this stage. To do this, naviate to here in an **administator** console: C:\Program Files (x86)\Apache Software Foundation\Apache2.2\bin and run the following command: `httpd.exe --console`. The console argument will ensure that you receive any error messages in the logs which you can use to rectify any problems at this stage.

## Configuring your Apache Server
Now that you have installed all of the necessary pieces of the autoreduction front-end setup, you will need to configure it to all work together. To do this, use the following steps:

1. Firstly, we need to make sure Apache pulls in our WSGI modules. To do this, we must add the following line to the 'includes section' of the httpd.conf (C:\Program Files (x86)\Apache Software Foundation\Apache2.2\conf\httpd.conf) file: `Include C:/autoreduce/WebApp/ISIS/autoreduce_webapp/apache/apache_django_wsgi.conf`
2. 
