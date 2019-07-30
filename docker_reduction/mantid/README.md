# Mantid Docker
To use this docker setup it is recommended that you do this from an ansible node to ensure the local environment is configured correctly.
However, this Dockerfile can be used without this but you must install the latest version of Docker and have cloned the autoreduction git repository.

### Manual use
Should you need to create and use the docker container for mantid manually you will need to firstly build the container.

***If you are at ISIS**:  It is important to remember **NOT** to use the live ISIS data archive or CEPH as these are production systems
 and should not be used for testing unless completely necessary.*

* Change directory to the directory containing the Mantid Dockerfile:

```$ cd docker_reduction/mantid```

* Build the docker file into an image:

```$ Docker build -t mantid-reduction-container . ```

* Run the image as a container:

```
$ Docker run  -v /path/to/local/input/directory:/isis/  \
              -v /path/to/local/output/directory:/instrument/  \
              -e SCRIPT=/path/to/reduction/script/inside/container  \
              -e INPUT_FILE=/path/to/input/data/inside/container  \
              -e OUTPUT_DIR=/path/to/output/directory/inside/container  \
              mantid-reduction-container
```

*Note that if you use the scripts and data from `docker_reduction/mantid/tests/input`* then the above looks like this:
 ```
$ Docker run  -v reduction_docker/mantid/tests/input:/isis/  \
              -v reduction_docker/mantid/tests/output:/instrument/  \
              -e SCRIPT=/isis/load_script.py  \
              -e INPUT_FILE=/isis/FakeWorkspace.nxs  \
              -e OUTPUT_DIR=/instrument/  \
              mantid-reduction-container
```
If you run this command, you will note that a file name 'load-successful.nxs' will be created inside `docker_reduction/mantid/tests/output`.
This means that the docker container is running successfully.

If you want to look inside the container for further manual testing change the run command like so:
```
$ Docker run  -v /path/to/local/input/directory:/isis/  \
              -v /path/to/local/output/directory:/instrument/  \
              -e SCRIPT=/path/to/reduction/script/inside/container  \
              -e INPUT_FILE=/path/to/input/data/inside/container  \
              -e OUTPUT_DIR=/path/to/output/directory/inside/container  \
              -it mantid-reduction-container /bin/bash
```
This will open a terminal inside the container.
