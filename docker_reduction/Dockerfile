FROM debian:latest
FROM python:buster

RUN mkdir /autoreduce
WORKDIR /autoreduce

RUN apt-get update && apt-get install -y sudo && apt-get install -y software-properties-common
# RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

ADD requirements.txt .

RUN python -m pip install -r requirements.txt

ADD ./build ./build
ADD ./setup.py .
# ADD test_credentials.log ./utils/test_credentials.ini
ADD ./monitors/test_settings.py ./monitors/test_settings.py
ADD ./utils/test_settings.py ./utils/test_settings.py

#this is a complete hack to fix a problem with the static files e.g css
#ADD test_settings.log ./WebApp/autoreduce_webapp/autoreduce_webapp/test_settings.py

ADD ./queue_processors/autoreduction_processor/test_settings.py ./queue_processors/autoreduction_processor/test_settings.py
ADD ./queue_processors/queue_processor/test_settings.py ./queue_processors/queue_processor/test_settings.py

RUN python -m pip install -e .

ADD . .

#ADD test_settings.log ./WebApp/autoreduce_webapp/autoreduce_webapp/test_settings.py
#ADD test_credentials.log ./utils/test_credentials.ini

RUN python setup.py test_settings
RUN python setup.py externals -s activemq
RUN python setup.py start
EXPOSE 8000
CMD ["python","WebApp/autoreduce_webapp/manage.py", "runserver", "0.0.0.0:8000"]

