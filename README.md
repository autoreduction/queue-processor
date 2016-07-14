# ISIS Autoreduction WebApp

- [Linux installation](#linux-installation)
- [Windows Installation](#windows-installation)

## Linux Installation

Recommended Server OS: Red Hat Enterprise Linux (RHEL) 6 / 7

***Note: Most, if not all, commands will need to be run as root. If using `sudo` please check the python note below***

## Red Hat 7
    
    wget http://repo.mysql.com/mysql-community-release-el7-5.noarch.rpm
    rpm -ivh mysql-community-release-el7-5.noarch.rpm

### Install prerequisites

1. `yum update`
2. `yum groupinstall 'development tools'`
3. `yum install zlib-devel bzip2-devel openssl-devel xz-libs wget httpd mod_wsgi mysql-devel python-devel python-pip httpd-devel.x86_64 mercurial`

### Install mod_wsgi
1. `wget https://github.com/GrahamDumpleton/mod_wsgi/archive/4.3.0.tar.gz`
2. `tar xvfz 4.3.0.tar.gz`
3. `cd mod_wsgi-4.3.0/`
4. `./configure --with-python=/usr/bin/python`
5. `make && make install`

### Install MySQL
1. `yum install mysql mysql-server MySQL-python`
2. `pip install mysql-python`

### Install Django
1. `pip install django==1.7.1`
2. `pip install pytz`

### Installing application

    git clone https://github.com/mantidproject/autoreduce.git /usr/src/autoreduce
    ln -s /usr/src/autoreduce/WebApp/ISIS/autoreduce_webapp /var/www/autoreduce_webapp
    ln -s /usr/lib/python2.7/site-packages/Django-1.7.1-py2.7.egg/django/contrib/admin/static/admin/ /var/www/autoreduce_webapp/static/admin

### Install ActiveMQ and stomp.py
    
Set up ActiveMQ as in the backend (`ISISPostProcessRPM`)

### Configure ActiveMQ
1. `adduser --system activemq`
2. `chown -R activemq: /opt/activemq/`
3. `nano /opt/activemq/conf/activemq.xml`
4. Change 


        <managementContext>
            <managementContext createConnector="false"/>
        </managementContext>

   to 

        <managementContext>`
            <managementContext createConnector="true"/>
        </managementContext>


5. `nano /etc/init.d/activemqstart.sh`

        #!/bin/bash
        export JAVA_HOME=/usr
        /opt/activemq/bin/activemq start &

6. `nano /etc/init.d/activemqstop.sh`

        #!/bin/bash
        export JAVA_HOME=/usr
        /opt/activemq/bin/activemq-admin stop

7. `nano /etc/init.d/activemq`
        
        #!/bin/bash
        #
        # activemq       Starts ActiveMQ.
        #
        # chkconfig: 345 88 12
        # description: ActiveMQ is a JMS Messaging Queue Server.
        ### BEGIN INIT INFO
        # Provides: $activemq
        ### END INIT INFO
         
        # Source function library.
        . /etc/init.d/functions
         
        [ -f /etc/init.d/activemqstart.sh ] || exit 0
        [ -f /etc/init.d/activemqstop.sh ] || exit 0
         
        RETVAL=0
         
        umask 077
         
        start() {
               echo -n $"Starting ActiveMQ: "
               daemon /etc/init.d/activemqstart.sh
               echo
               return $RETVAL
        }
        stop() {
               echo -n $"Shutting down ActiveMQ: "
               daemon su -c /etc/init.d/activemqstop.sh activemq
               echo
               return $RETVAL
        }
        restart() {
               stop
               start
        }
        case "$1" in
        start)
               start
               ;;
        stop)
               stop
               ;;
        restart|reload)
               restart
               ;;
        *)
               echo $"Usage: $0 {start|stop|restart}"
               exit 1
        esac
         
        exit $?

8. `chmod +x /etc/init.d/activemqstart.sh && chmod +x /etc/init.d/activemqstop.sh && chmod +x /etc/init.d/activemq`
9. `chkconfig --add activemq`
10. `chkconfig activemq on`
11. `firewall-cmd --add-port=61613/tcp --permanent && firewall-cmd --reload && firewall-cmd --add-port=61613/tcp` (Ignore the warning)

### Checking everything is working
1. Modify `simple_stop_test.py` by changing `localhost` to the correct hostname, and the credentials `uname` and `upass` as were set in `nano /opt/activemq/conf/activemq.xml` under `<simpleAuthenticationPlugin>`
2. `python simple_stomp_test.py`
3. Expected output:

        Starting connection
        subscribing
        sending
        sent
        received a message
        
### Setting up Priority Queues for ActiveMQ
1. `nano /opt/activemq/conf/activemq.xml`
2. Within the `<policyEntries>` tag include `<policyEntry queue=">" queuePrefetch="1" prioritizedMessages="true" useCache="false" expireMessagesPeriod="0"/>`

### Installing ICAT support
1. `pip install suds-jurko==0.6` (this may require `easy_install -U setuptools`).
4. `wget https://icatproject.org/misc/python-icat/download/python-icat-0.5.1.tar.gz`
5. `tar xzf python-icat-0.5.1.tar.gz`
6. `cd python-icat-0.5.1`
7. `python setup.py build`
8. `python setup.py install`
9. Set the correct values for ICAT in `autoreduce_webapp/autoreduce_webapp/settings.py` -- ? also activemq creds

### Setting up MySQL
1. `service mysqld start`
2. `/usr/bin/mysql_secure_installation`
3. `mysql -u root -p`
4. `CREATE DATABASE autoreduction;`
5. `CREATE USER 'autoreduce'@'*' IDENTIFIED BY 'password';`
6. `GRANT ALL ON autoreduction.* TO 'autoreduce'@'localhost' IDENTIFIED BY 'password';`
7. `GRANT ALL ON test_autoreduction.* TO 'autoreduce'@'localhost' IDENTIFIED BY 'password';`
8. `exit`
8. `python /var/www/autoreduce_webapp/manage.py migrate`
9. Add `max_allowed_packet=64M` to `/etc/my.cnf`
10. `service mysqld restart`

### Setting up Apache
1. `firewall-cmd --add-port=80/tcp --permanent && firewall-cmd --reload && firewall-cmd --add-port=80/tcp`
2. `cp ~/autoreduce/WebApp/ISIS/apache_autoreduce_webapp.conf /etc/httpd/conf.d/`
3. `service httpd restart`
4. Enable autostart: `systemctl enable httpd`

500 errors can be caused by SELinux policies restricting Apache's access to files and the network. `setsebool -P httpd_can_network_connect 1` will allow it to connect to MySQL. You may need to run `chcon -v --type=httpd_sys_ra_content_t yourlogfile.log` for the log file set in `/usr/src/autoreduce/WebApp/ISIS/autoreduce_webapp/autoreduce_webapp/settings.py` (`LOG_FILE`). All errors can be fixed automatically by

    grep httpd /var/log/audit/audit.log | audit2allow -M httpd-policy
    semodule -i httpd-policy





## Windows Installation

Recommended Server: Windows Server 2012

Note: Git Bash is the recommended command line (after step 4). Any command line terminal will need re-opening to pick up any new entries in the PATH environmental variables.

### Install prerequisites

1. Download and install Python 2.7 from: https://www.python.org/downloads/windows/
2. Add `c:\Python27` to the PATH environmental variable.
3. Download and install 7-Zip from: http://downloads.sourceforge.net/sevenzip/7z920.exe
4. Download and install MySqlServer from: http://dev.mysql.com/downloads/windows/installer/5.6.html
5. Download and install Git from: http://git-scm.com/download/win
6. Download and install MySQL-Python from: http://www.lfd.uci.edu/~gohlke/pythonlibs/4y6heurj/MySQL-python-1.2.5.win-amd64-py2.7.exe
7. Download and install Mercurial from: https://bitbucket.org/tortoisehg/files/downloads/mercurial-3.1.2-x64.msi
8. Download and install http://downloads.sourceforge.net/project/pywin32/pywin32/Build%20219/pywin32-219.win-amd64-py2.7.exe?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fpywin32%2Ffiles%2Fpywin32%2FBuild%2520219%2F&ts=1416304230&use_mirror=garr
9. Download https://raw.github.com/pypa/pip/master/contrib/get-pip.py and run `python get-pip.py`
10. Add `c:\python27\scripts` to the path environmental variable.
11. `pip install django`

### Configuring MySQL

1. `mysql.exe -u root -p`
2. `CREATE DATABASE autoreduction;`
3. `CREATE USER 'autoreduce'@'*' IDENTIFIED BY 'password';`
4. `GRANT ALL ON autoreduction.* TO 'autoreduce'@'localhost' IDENTIFIED BY 'password';`
5. `GRANT ALL ON test_autoreduction.* TO 'autoreduce'@'localhost' IDENTIFIED BY 'password';`
6. `exit`
7. Edit `C:\ProgramData\MySQL\MySQL Server 5.6\my.cnf` changing `max_allowed_packet=4M` to `max_allowed_packet=64M`

### Install ICAT client

1. `hg clone https://AverageMarcus@bitbucket.org/AverageMarcus/suds -u release-0.6.1`
2. `cd suds`
3. `python setup.py install`
4. Download and extract (using 7-zip): http://icatproject.googlecode.com/svn/contrib/python-icat/python-icat-0.5.1.tar.gz
5. `cd python-icat-0.5.1`
6. `python setup.py build`
7. `python setup.py install`
8. Set the correct values for ICAT in `autoreduce_webapp/autoreduce_webapp/settings.py`

### Install application

1. `git clone https://github.com/mantidproject/autoreduce.git`
2. Copy `C:\Python27\Lib\site-packages\django\contrib\admin\static\admin` into `autoreduce_webapp\static\`

### Configure IIS

1. Enable IIS Role through the Server Manager dashboard and ensure CGI is selected.
2. Open IIS Manager and double click on `FastCGI Settings`
3. Click `Add application` and enter the following:
        
Full Path: `C:\Python27\python.exe`

Arguments: `C:\[PATH TO WEBAPP]\autoreduce_webapp\manage.py fcgi --pythonpath=C:\[PATH TO WEBAPP]\autoreduce_webapp --settings=autoreduce_webapp.settings`

4. Create a new web application pointing at the root of the web app 
5. Create `web.config` in the root of the web application and enter the following:

          <?xml version="1.0" encoding="UTF-8"?>
          <configuration>
            <system.webServer>
              <handlers>
                <clear/>
                <add name="FastCGI" path="*" verb="*" modules="FastCgiModule" scriptProcessor="C:\Python27\python.exe|C:\[PATH TO WEBAPP]\autoreduce_webapp\manage.py fcgi --pythonpath=C:\[PATH TO WEBAPP]\autoreduce_webapp --settings=autoreduce_webapp.settings" resourceType="Unspecified" requireAccess="Script" />
              </handlers>
            </system.webServer>
          </configuration>

6. Double click `Feature Delegation` followed by clicking `Custom Site Delegation`.
7. Select the newly created website from the dropdown and change `CGI` and `Handler Mappings` to Read/Write
8. Create `web.config` in the `static` directory with the following:

          <?xml version="1.0" encoding="UTF-8"?>
          <configuration>
            <system.webServer>
              <!-- this configuration overrides the FastCGI handler to let IIS serve the static files -->
              <handlers>
              <clear/>
                <add name="StaticFile" path="*" verb="*" modules="StaticFileModule" resourceType="File" requireAccess="Read" />
              </handlers>
            </system.webServer>
          </configuration>

9. Change the security permissions for the `static` folder and give `IUSR` Read & execute permission.

## Settings to add

There are a few optional settings that the app looks for from the "Settings" table in the database. These are:

`support_email` - Shown in the footer as a "contact us" email link.
`admin_email` - Shown on error pages as an email link to report issues.
`ICAT_YEARS_TO_SHOW` - The number of years worth of data to retrieve from ICAT for use in populating the run list. This defaults to 3 years.

## Installing the Queue Processor service

1. In an administrative command prompt navigate to the autoreduce_webapp folder
2. `python queue_processor_win_service.py install`
3. Open Services, right click on "Autoreduce Queue Processor" and select Properties
4. Change Startup Type to Automatic
5. Click Start
