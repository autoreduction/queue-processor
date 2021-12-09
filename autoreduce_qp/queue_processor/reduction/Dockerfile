FROM ghcr.io/autoreduction/autoreduce:latest
COPY . .
RUN export DEBIAN_FRONTEND=noninteractive
ARG DEBIAN_FRONTEND=noninteractive
RUN python3 -m pip install autoreduce-qp==22.0.0.dev22 --extra-index-url https://api.packagr.app/public
RUN pip install pytest
RUN pip install parameterized
#RUN pip install autoreduce-qp --extra-index-url https://api.packagr.app/public
USER isisautoreduce
