FROM ghcr.io/autoreduction/base

# Installs queue-processor from your local repository
ADD . .
RUN python3 -m pip install --user --no-cache-dir .

CMD autoreduce-qp-start
