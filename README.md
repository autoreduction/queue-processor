# ISIS Autoreduction WebApp

## Installation

Recommended Server OS: Red Hat 6

***Note: Most, if not all, commands will need to be run as root. If using `sudo` please check the python note below***

### Install prerequisites
1. `yum update`
2. `yum groupinstall 'development tools'`
3. `yum install zlib-devel bzip2-devel openssl-devel xz-libs wget httpd mod_wsgi mysql-devel python-devel httpd-devel.x86_64`

### Install Python 2.7
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
14. `lokkit --port=61613:tcp`

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

### Setting up MySQL
1. `service mysqld start`
2. `/usr/bin/mysql_secure_installation`
3. `mysql -u admin -p`
4. `CREATE DATABASE autoreduction`
5. `CREATE USER 'autoreduce'@'*' IDENTIFIED BY 'password';`
6. `GRANT ALL ON 'autoreduction'.* TO 'autoreduce'@'*' IDENTIFIED BY 'password';`
7. `GRANT ALL ON 'test_autoreduction'.* TO 'autoreduce'@'*' IDENTIFIED BY 'password';`
8. `python /var/www/autoreduce_webapp/manage.py syncdb`
9. Add `max_allowed_packet=64M` to `/etc/my.cnf`

### Setting up Apache
1. `lokkit --port=80:tcp`
2. Copy `apache_auto_reduce_webapp.conf` to `/etc/httpd/conf.d/`
3. `service httpd restart`

### Installing application
1. `git clone https://github.com/mantidproject/autoreduce.git`
2. `ln -s ./autoreduce/WebApp/ISIS/autoreduce_webapp /var/www/autoreduce_webapp`
4. `mkdir /var/www/autoreduce_webapp/static`
5. `ln -s /usr/local/lib/python2.7/site-packages/django/contrib/admin/static/admin/ /var/www/autoreduce_webapp/static/admin`

### Installing ICAT support
1. `pip install suds-jurko`
2. `wget http://icatproject.googlecode.com/svn/contrib/python-icat/python-icat-0.5.1.tar.gz`
3. `tar xzf python-icat-0.5.1.tar.gz`
4. `cd python-icat-0.5.1`
5. `python setup.py build`
6. `python setup.py install`