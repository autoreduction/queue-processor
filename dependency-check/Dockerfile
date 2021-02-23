FROM centos/python-36-centos7

USER root

COPY . /autoreduce

WORKDIR /autoreduce

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

RUN pip install -e .
