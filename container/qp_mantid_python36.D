FROM ghcr.io/autoreduction/base

USER root
RUN export DEBIAN_FRONTEND=noninteractive && apt-add-repository "deb [arch=amd64] http://apt.isis.rl.ac.uk $(lsb_release -c | cut -f 2) main" &&\
  apt-add-repository ppa:mantid/mantid &&\
  apt-get update &&\
  apt-get install -y libglu1-mesa mantid &&\
  apt-get clean &&\
  cp /opt/Mantid/bin/Mantid.properties /opt/Mantid/lib/Mantid.properties

USER isisautoreduce
RUN python3 -m pip install --user autoreduce_qp==22.0.0.dev20
USER root
RUN python3 -m pip uninstall -y h5py && apt install --reinstall -y python3-h5py

USER isisautoreduce
WORKDIR /home/isisautoreduce
ENV PYTHONPATH=/opt/Mantid/scripts/:/opt/Mantid/scripts/Diffraction/:/opt/Mantid/scripts/Engineering/:/opt/Mantid/bin:/opt/Mantid/lib:/opt/Mantid/plugins:/opt/Mantid/scripts/SANS/:/opt/Mantid/scripts/Inelastic/:/opt/Mantid/scripts/ExternalInterfaces:/opt/Mantid/scripts/Interface

CMD autoreduce-qp-start
