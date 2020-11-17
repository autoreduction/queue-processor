FROM python:3.8.6-buster

COPY ./ /autoreduce

RUN apt-get update  && apt-get install -y \
    chromium

RUN wget -q "https://chromedriver.storage.googleapis.com/86.0.4240.22/chromedriver_linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /usr/bin/ \
    && rm /tmp/chromedriver.zip





WORKDIR /autoreduce


RUN pip install concurrencytest

ENTRYPOINT ["python",  "webtests/runner.py", "-u", "http://172.31.51.54:8000"]




