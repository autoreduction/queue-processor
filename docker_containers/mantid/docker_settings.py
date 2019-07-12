"""
Contains mount settings for docker
This does not need to be private
"""


class Mount(object):
    """ Class to contain information about a docker mount"""

    def __init__(self, host_location, container_destination):
        # The location of the directory you wish to mount on the host machine
        self.host_location = host_location
        # The location of the desire destination to mount to on the container
        self.container_destination = container_destination


# On production this will be the base directory of the ISIS data archive (/isis)
DATA_IN = Mount(host_location='/isis/',
                container_destination='/isis/')

# On production this will be the base directory of CEPH (/instrument)
DATA_OUT = Mount(host_location='/instrument/',
                 container_destination='/instrument/')
