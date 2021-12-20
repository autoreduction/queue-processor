FROM ghcr.io/autoreduction/autoreduce:latest
COPY . .
RUN export DEBIAN_FRONTEND=noninteractive
ARG DEBIAN_FRONTEND=noninteractive
RUN python3 -m pip install autoreduce-qp==22.0.0.dev38 --extra-index-url https://api.packagr.app/public
RUN python3 -m pip install pytest
RUN python3 -m pip install parameterized
USER root
RUN mkdir -p /instrument
RUN mkdir -p /isis
RUN chmod 777 /instrument
RUN chmod 777 /isis
USER isisautoreduce
