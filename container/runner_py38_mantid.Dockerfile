FROM continuumio/miniconda3 AS build

ARG MANTID_VERSION
WORKDIR /app
ADD . .

# Install conda-pack into the base environment
RUN conda install conda-pack

# Create the conda environment
RUN conda create -n py38 python=3.8.12

# Make RUN, CMD, and ENTRYPOINT commands use the new environment with the SHELL command
SHELL [ "conda", "run", "-n", "py38", "/bin/bash", "-c" ]

# Install Mantid and install autoreduce-qp from local directory
RUN conda config --add channels conda-forge
RUN conda install mantid=${MANTID_VERSION} -c mantid
RUN python3 -m pip install --no-cache-dir . 

# Use conda-pack to create a standalone enviornment in /venv:
RUN conda-pack -n py38 -o /tmp/env.tar && \
    mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
    rm /tmp/env.tar

RUN cp /venv/bin/Mantid.properties /venv/lib/Mantid.properties

# We've put venv in same path it'll be in final image,
# so now fix up paths:
RUN /venv/bin/conda-unpack



FROM debian:buster AS runtime

RUN useradd -m --no-log-init -s /bin/bash -u 880844730 isisautoreduce
USER isisautoreduce
WORKDIR /home/isisautoreduce

COPY --from=build /venv /venv
SHELL [ "source", "/venv/bin/activate", "/bin/bash", "-c" ]

ENV PYTHONPATH=/venv/scripts/:/venv/scripts/Diffraction/:/venv/scripts/Engineering/:/venv/bin:/venv/lib:/venv/plugins:/venv/scripts/SANS/:/venv/scripts/Inelastic/:/venv/scripts/ExternalInterfaces:/venv/scripts/Interface
CMD autoreduce-qp-start
