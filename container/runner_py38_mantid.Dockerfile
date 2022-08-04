FROM condaforge/mambaforge AS build

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
RUN mamba install conda-pack

RUN mamba env create -f environment.yml
# Make RUN, CMD, and ENTRYPOINT commands use the new environment with the SHELL command
SHELL [ "mamba", "run", "-n", "py38", "/bin/bash", "-c" ]

# Install Mantid
RUN if [ "$NIGHTLY" = "False" ]; then \
    mamba install mantid -c mantid; \
    else \
    mamba install -c mantid/label/nightly mantid; \
    fi

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
    gcc \
    libgl1-mesa-glx

RUN groupadd -g 880844730 isisautoreduce \
    && useradd -u 880844730 -g 880844730 -m -s /bin/bash --no-log-init isisautoreduce
USER isisautoreduce
WORKDIR /home/isisautoreduce

COPY --from=build /venv /venv

ENV PYTHONPATH=/venv/scripts/:/venv/scripts/Diffraction/:/venv/scripts/Engineering/:/venv/bin:/venv/lib:/venv/plugins:/venv/scripts/SANS/:/venv/scripts/Inelastic/:/venv/scripts/ExternalInterfaces:/venv/scripts/Interface

# Add the environment to the PATH (equivalent of running source /venv/bin/activate)
ENV PATH="/venv/bin:$PATH"

# When the image is run, run the code with the environment
SHELL [ "/bin/bash", "-c" ]
CMD autoreduce-qp-start
