import docker


def test_reduction_pytests():
    """Runs the tests located in reduction/tests within the docker container"""

    # Return a client configured from environment variables
    # The environment variables used are the same as those used by the Docker command-line client
    # https://docs.docker.com/engine/reference/commandline/cli/#environment-variables

    client = docker.from_env()
    args = ["pytest", "tests/"]
    container = client.containers.create(
        'ghcr.io/autoreduction/runner-mantid:6.2.0',
        command="/bin/sh",
        tty=True,
        environment=["AUTOREDUCTION_PRODUCTION=1"],
        stdin_open=True,
        detach=True,
    )

    container.start()
    container.exec_run(cmd=args)
    container.stop()
