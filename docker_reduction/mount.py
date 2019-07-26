"""
A Class to store information about a docker mount
"""


class Mount(object):
    """ Class to contain information about a docker mount """

    def __init__(self, host_location, container_destination):
        # The location of the directory you wish to mount on the host machine
        self.host_location = host_location
        # The location of the desired destination to mount to on the container
        self.container_destination = container_destination
