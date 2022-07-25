FROM continuumio/miniconda3 AS build

ARG NIGHTLY=False
WORKDIR /app
ADD . .

RUN export DEBIAN_FRONTEND=noninteractive && apt-get update &&\
    apt-get install -y \
    wget \
    gnupg \
    git \
    software-properties-common \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    gcc

# Install conda-pack into the base environment
RUN conda install conda-pack

# Create the conda environment
RUN conda create -n py38 python=3.8.12

# Make RUN, CMD, and ENTRYPOINT commands use the new environment with the SHELL command
SHELL [ "conda", "run", "-n", "py38", "/bin/bash", "-c" ]

# Install Mantid and install autoreduce-qp from local directory
RUN conda config --add channels conda-forge
RUN if [ "$NIGHTLY" = "False" ]; then \
    conda install mantid -c mantid; \
    else \
    conda install -c mantid/label/nightly mantid; \
    fi

RUN python3 -m pip install --no-cache-dir . 
RUN python3 -m pip install --no-cache-dir mysqlclient debugpy

# Use conda-pack to create a standalone enviornment in /venv:
RUN conda-pack -n py38 -o /tmp/env.tar && \
    mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
    rm /tmp/env.tar

RUN cp /venv/bin/Mantid.properties /venv/lib/Mantid.properties

# We've put venv in same path it'll be in final image,
# so now fix up paths:
RUN /venv/bin/conda-unpack



FROM debian:buster AS runtime

RUN export DEBIAN_FRONTEND=noninteractive && apt-get update &&\
    apt-get install -y \
    wget \
    gnupg \
    git \
    software-properties-common \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    gcc

RUN useradd -m --no-log-init -s /bin/bash -u 880844730 isisautoreduce
USER isisautoreduce
WORKDIR /home/isisautoreduce

COPY --from=build /venv /venv

ENV PYTHONPATH=/venv/scripts/:/venv/scripts/Diffraction/:/venv/scripts/Engineering/:/venv/bin:/venv/lib:/venv/plugins:/venv/scripts/SANS/:/venv/scripts/Inelastic/:/venv/scripts/ExternalInterfaces:/venv/scripts/Interface

# Add the environment to the PATH (equivalent of running source /venv/bin/activate)
ENV PATH="/venv/bin:$PATH"

# When the image is run, run the code with the environment
SHELL [ "/bin/bash", "-c" ]
CMD autoreduce-qp-start
