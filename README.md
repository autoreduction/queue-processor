# ISIS Autoreduction WebApp

- [Linux installation](#Linux-Installation)
- [Windows Installation](#Windows-Installation)

## Linux Installation

Recommended Server OS: Red Hat 6 / Red Hat 7

***Note: Most, if not all, commands will need to be run as root. If using `sudo` please check the python note below***

### Red Hat 7 Only
1. `wget http://repo.mysql.com/mysql-community-release-el7-5.noarch.rpm`
2. `rpm -ivh mysql-community-release-el7-5.noarch.rpm`

### Install prerequisites
1. `yum update`
2. `yum groupinstall 'development tools'`
3. `yum install zlib-devel bzip2-devel openssl-devel xz-libs wget httpd mod_wsgi mysql-devel python-devel httpd-devel.x86_64 mercurial`

### Install Python 2.7 (Not required for Red Hat 7)
**Note: Do not remove python 2.6! Ensure that you specify python 2.7 correctly when using sudo commands as it will default to the installed.**

1. `wget http://www.python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz`
2. `xz -d Python-2.7.6.tar.xz`
3. `tar -xvf Python-2.7.6.tar`
4. `cd Python-2.7.6`
5. `./configure --prefix=/usr/local --enable-shared`
6. `make && make install`
7. `ln -s /usr/local/lib/libpython2.7.so.1.0 /usr/lib/libpython2.7.so.1.0`
8. `ldconfig /usr/local/bin/python`
9. `export PATH="/usr/local/bin:$PATH"`

### Install mod_wsgi
1. `wget https://github.com/GrahamDumpleton/mod_wsgi/archive/4.3.0.tar.gz`
2. `tar xvfz 4.3.0.tar.gz`
3. `cd mod_wsgi-4.3.0/`
4. `./configure --with-python=/usr/local/bin/python`
5. `make && make install`

### Install Pip and easy_install
1. `wget --no-check-certificate https://pypi.python.org/packages/source/s/setuptools/setuptools-1.4.2.tar.gz`
2. `tar -xvf setuptools-1.4.2.tar.gz`
3. `cd setuptools-1.4.2`
4. `python setup.py install`
5. `wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py`
6. `python get-pip.py`

### Install MySQL
1. `yum install mysql mysql-server MySQL-python`
2. `pip install mysql-python`

### Install Django
1. `easy_install Django`
2. `pip install pytz`

### Installing application
1. `git clone https://github.com/mantidproject/autoreduce.git /usr/src/autoreduce`
2. `ln -s /usr/src/autoreduce/WebApp/ISIS/autoreduce_webapp /var/www/autoreduce_webapp`
3. `ln -s /usr/local/lib/python2.7/site-packages/django/contrib/admin/static/admin/ /var/www/autoreduce_webapp/static/admin` Red Hat 6 Only
3. `ln -s /usr/lib/python2.7/site-packages/Django-1.7.1-py2.7.egg/django/contrib/admin/static/admin/ /var/www/autoreduce_webapp/static/admin` Red Hat 7 Only

### Install ActiveMQ and stomp.py
1. `wget http://mirror.gopotato.co.uk/apache/activemq/5.9.1/apache-activemq-5.9.1-bin.tar.gz`
2. `tar xzf apache-activemq-5.9.1-bin.tar.gz`
3. `mv apache-activemq-5.9.1 /opt`
4. `ln -sf /opt/apache-activemq-5.6.0/ /opt/activemq`
5. `easy_install stomp.py`

### Configure ActiveMQ
1. `adduser --system activemq`
2. `chown -R activemq: /opt/apache-activemq-5.9.1/`
3. `nano /opt/apache-activemq-5.9.1/conf/activemq.xml`
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
        /opt/apache-activemq-5.9.1/bin/activemq start &

6. `nano /etc/init.d/activemqstop.sh`

        #!/bin/bash
        export JAVA_HOME=/usr
        /opt/apache-activemq-5.9.1/bin/activemq-admin stop

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
11. `/opt/apache-activemq-5.9.1/bin/activemq setup /etc/default/activemq`
12. `chown root /etc/default/activemq`
13. `chmod 600 /etc/default/activemq`
14. `lokkit --port=61613:tcp` Red Hat 6 Only
    `firewall-cmd --add-port=61613/tcp --permanent && firewall-cmd --reload && firewall-cmd --add-port=61613/tcp` Read Hat 7 Only (Ignore the warning)

### Checking everything is working
1. Modify `simple_stop_test.py` by changing `localhost` to the correct hostname.
2. `python simple_stomp_test.py`
3. Expected output:

        Starting connection
        subscribing
        sending
        sent
        received a message

### Setting credentials for ActiveMQ
1. `nano /opt/apache-activemq-5.9.1/conf/activemq.xml`
2. Include the following within the `<broker>` tag with the desired values
        
        <plugins>
            <simpleAuthenticationPlugin>
                <users>
                    <authenticationUser username="admin" password="pa$$w0rd"
                        groups="users,admins"/>
                </users>
            </simpleAuthenticationPlugin>
        </plugins>


### Installing ICAT support
1. `hg clone https://AverageMarcus@bitbucket.org/AverageMarcus/suds -u release-0.6.1`
2. `cd suds`
3. `python setup.py install`
4. `wget http://icatproject.googlecode.com/svn/contrib/python-icat/python-icat-0.5.1.tar.gz`
5. `tar xzf python-icat-0.5.1.tar.gz`
6. `cd python-icat-0.5.1`
7. `python setup.py build`
8. `python setup.py install`
9. Set the correct values for ICAT in `autoreduce_webapp/autoreduce_webapp/settings.py`

### Setting up MySQL
1. `service mysqld start`
2. `/usr/bin/mysql_secure_installation`
3. `mysql -u admin -p` on Red Hat 6. `mysql -u root -p` on Red Hat 7
4. `CREATE DATABASE autoreduction;`
5. `CREATE USER 'autoreduce'@'*' IDENTIFIED BY 'password';`
6. `GRANT ALL ON autoreduction.* TO 'autoreduce'@'localhost' IDENTIFIED BY 'password';`
7. `GRANT ALL ON test_autoreduction.* TO 'autoreduce'@'localhost' IDENTIFIED BY 'password';`
8. `exit`
8. `python /var/www/autoreduce_webapp/manage.py syncdb`
9. Add `max_allowed_packet=64M` to `/etc/my.cnf`
10. `service mysqld restart`

### Setting up Apache
1. `lokkit --port=80:tcp` Red Hat 6 Only
1. `firewall-cmd --add-port=80/tcp --permanent && firewall-cmd --reload && firewall-cmd --add-port=80/tcp` Red Hat 7 Only
2. Copy `apache_auto_reduce_webapp.conf` to `/etc/httpd/conf.d/`
3. `service httpd restart`


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
8. Download https://raw.github.com/pypa/pip/master/contrib/get-pip.py and run `python get-pip.py`
9. Add `c:\python27\scripts` to the path environmental variable.
10. `pip install django`

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

1. `git clone https://github.com/mantidproject/autoreduce.git /usr/src/autoreduce`
2. Copy `C:\Python27\Lib\site-packages\django\contrib\admin\static\admin` into `autoreduce_webapp\static\`

### Configure IIS

1. Enable IIS Role through the Server Manager dashboard and ensure CGI is selected.
2. Open IIS Manager and double click on `FastCGI Settings`
3. Click `Add application` and enter the following:
        
  Full Path: C:\Python27\python.exe
  Arguments: C:\[PATH TO WEBAPP]\autoreduce_webapp\manage.py fcgi --pythonpath=C:\[PATH TO WEBAPP]\autoreduce_webapp --settings=autoreduce_webapp.settings

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