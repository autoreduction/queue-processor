# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module that reads from the reduction pending queue and calls the python script on that data.
"""
import os
import subprocess
import sys

import stomp

from twisted.internet import reactor

from model.message.message import Message
from queue_processors.autoreduction_processor.autoreduction_logging_setup import logger
# pylint:disable=no-name-in-module,import-error
from queue_processors.autoreduction_processor.settings import MISC
from utils.clients.queue_client import QueueClient


class Listener(stomp.ConnectionListener):
    """ Listener class that is used to consume messages from ActiveMQ. """
    def __init__(self):
        """ Initialise listener. """
        self.proc_list = []
        self.rb_list = []  # list of RB numbers of active reduction runs
        self.cancel_list = []  # list of (run number, run version)s to drop (once) used

    @staticmethod
    # pylint:disable=arguments-differ
    def on_error(message):
        """ Handler for errored messages. """
        logger.error("Error message received - %s", str(message))

    # pylint:disable=arguments-differ
    def on_message(self, headers, data):
        """ handles message consuming. It will consume a message. """
        destination = headers['destination']
        logger.debug("Received frame destination: %s", destination)
        logger.debug("Received frame priority: %s", headers["priority"])

        self.update_child_process_list()
        message = Message()
        message.populate(data)

        if message.cancel:
            self.add_cancel(message)
            return

        self.hold_message(destination, data, headers)

    def hold_message(self, destination, data, headers):
        """ Calls the reduction script. """
        logger.debug("holding thread")
        message = Message()
        message.populate(data)

        self.update_child_process_list()
        if not self.should_proceed(message):  # wait while the run shouldn't proceed
            # pylint: disable=maybe-no-member
            reactor.callLater(10, self.hold_message,  # pragma: no cover
                              destination, data,
                              headers)

            return

        if self.should_cancel(message):
            self.cancel_run(message)  # pylint: disable=maybe-no-member
            return


        if not os.path.isfile(MISC['post_process_directory']):
            logger.warning("Could not find autoreduction post processing file "
                           "- please contact a system administrator")
        python_path = sys.executable
        logger.info("Calling: %s %s %s %s",
                    python_path, MISC['post_process_directory'], destination,
                    message.serialize())    # TODO: limit reduction script  #pylint:disable=fixme
        proc = subprocess.Popen([python_path,
                                 MISC['post_process_directory'],
                                 destination,
                                 message.serialize()])  # PPA expects json data
        self.add_process(proc, message)

    def update_child_process_list(self):
        """ Updates the list of processes by checking they still exist. """
        for process in self.proc_list:
            if process.poll() is not None:
                index = self.proc_list.index(process)
                self.proc_list.pop(index)
                self.rb_list.pop(index)

    def add_process(self, proc, message):
        """ Add child process to list. """
        logger.info("Entered add_process. proc=%s message=%s", proc, message)
        self.proc_list.append(proc)
        self.rb_list.append(message.rb_number)

    def should_proceed(self, message):
        """ Check whether there's a job already running with the same RB. """
        if message.rb_number in self.rb_list:
            logger.info("Duplicate RB run #%s, waiting for the first to finish.",
                        message.rb_number)
            return False
        # else return True
        return True

    @staticmethod
    def run_tuple(message):
        """ return the tuple of (run_number, run version) from a dictionary. """
        run_number = message.run_number
        run_version = message.run_version
        if run_version is None:
            run_version = 0
        return run_number, run_version

    def add_cancel(self, message):
        """ Add this run to the cancel list, to cancel it next time it comes up. """
        tup = self.run_tuple(message)
        if tup not in self.cancel_list:
            self.cancel_list.append(tup)

    def should_cancel(self, message):
        """ Return whether a run is in the list of runs to be canceled. """
        tup = self.run_tuple(message)
        return tup in self.cancel_list

    def cancel_run(self, message):
        """ Cancel the reduction run. """
        tup = self.run_tuple(message)
        self.cancel_list.remove(tup)


class Consumer:
    # pylint: disable=too-few-public-methods
    """ Class used to setup the queue listener. """
    def __init__(self):
        """ Initialise consumer. """
        self.consumer_name = "autoreduction_processor"

    def run(self):
        """
        Connect to ActiveMQ via the QueueClient and listen to the
        /ReductionPending queue for messages.
        """
        activemq_client = QueueClient()
        activemq_client.connect()
        activemq_client.subscribe_amq(consumer_name=self.consumer_name,
                                      listener=Listener())


def main():  # pragma: no cover
    """ Main method, starts consumer. """
    logger.info("Start post process asynchronous listener!")
    # pylint: disable=maybe-no-member
    reactor.callWhenRunning(Consumer().run)
    reactor.run()
    logger.info("Stop post process asynchronous listener!")


if __name__ == '__main__':  # pragma: no cover
    main()
