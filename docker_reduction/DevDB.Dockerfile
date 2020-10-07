FROM mysql:5.7


# Installs system Python3, and the mysql client that is missing from this image
RUN apt-get update && apt-get install -y python3 python3-pip libmysqlclient-dev git

ADD setup.py /autoreduction/setup.py
ADD requirements.txt /autoreduction/requirements.txt
ADD build /autoreduction/build


WORKDIR /autoreduction
RUN pip3 install -e . && pip3 install -r requirements.txt

ADD utils /autoreduction/utils
ADD monitors /autoreduction/monitors
ADD WebApp /autoreduction/WebApp
ADD queue_processors /autoreduction/queue_processors

RUN python3 setup.py test_settings

### Database setup

# Adds permissions for the test-user to the autoreduction table
ENV MYSQL_ALLOW_EMPTY_PASSWORD=true

# Makes `python` also be provided by /usr/bin/python3.
# This fixes an issue with Django looking for Python when `python3 setup.py database` gets called
RUN update-alternatives --install "/usr/bin/python" "python" "/usr/bin/python3" 1

# Add the whole dir as late as possible to reduce what triggers a full docker rebuild
ADD . /autoreduction
ADD docker_reduction/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]