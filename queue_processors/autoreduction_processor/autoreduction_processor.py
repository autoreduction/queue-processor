# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module that reads from the reduction pending queue and calls the python script on that data.
"""
import json
import os
import subprocess
import sys

import stomp

from twisted.internet import reactor

from queue_processors.autoreduction_processor.autoreduction_logging_setup import logger
# pylint:disable=no-name-in-module,import-error
from queue_processors.autoreduction_processor.settings import MISC
from utils.clients.queue_client import QueueClient


class Listener(stomp.ConnectionListener):
    """ Listener class that is used to consume messages from ActiveMQ. """
    def __init__(self):
        """ Initialise listener. """
        logger.info("ARP Entered Listener.__init__")
        self.proc_list = []
        self.rb_list = []  # list of RB numbers of active reduction runs
        self.cancel_list = []  # list of (run number, run version)s to drop (once) used

    @staticmethod
    # pylint:disable=arguments-differ
    def on_error(message):
        """ Handler for errored messages. """
        logger.info("ARP Entered on_error")
        logger.error("Error message received - %s", str(message))

    # pylint:disable=arguments-differ
    def on_message(self, headers, data):
        """ handles message consuming. It will consume a message. """
        logger.info("ARP Entered on_message")
        destination = headers['destination']
        logger.debug("Received frame destination: %s", destination)
        logger.debug("Received frame priority: %s", headers["priority"])

        self.update_child_process_list()
        data_dict = json.loads(data)

        if "cancel" in data_dict and data_dict["cancel"]:
            self.add_cancel(data_dict)
            return

        self.hold_message(destination, data, headers)

    def hold_message(self, destination, data, headers):
        """ Calls the reduction script. """
        logger.info("ARP Entered hold_message")
        logger.debug("holding thread")
        data_dict = json.loads(data)

        self.update_child_process_list()
        if not self.should_proceed(data_dict):  # wait while the run shouldn't proceed
            # pylint: disable=maybe-no-member
            reactor.callLater(10, self.hold_message,  # pragma: no cover
                              destination, data,
                              headers)

            return

        if self.should_cancel(data_dict):
            self.cancel_run(data_dict)  # pylint: disable=maybe-no-member

            return

        print_dict = data_dict.copy()
        print_dict.pop("reduction_script")
        if not os.path.isfile(MISC['post_process_directory']):
            logger.warning("Could not find autoreduction post processing file "
                           "- please contact a system administrator")
        python_path = sys.executable
        logger.info("Calling: %s %s %s %s",
                    python_path, MISC['post_process_directory'], destination, print_dict)
        proc = subprocess.Popen([python_path,
                                 MISC['post_process_directory'],
                                 destination,
                                 data])
        self.add_process(proc, data_dict)

    def update_child_process_list(self):
        """ Updates the list of processes by checking they still exist. """
        logger.info("ARP Entered update_child_process_list")
        for process in self.proc_list:
            if process.poll() is not None:
                index = self.proc_list.index(process)
                self.proc_list.pop(index)
                self.rb_list.pop(index)

    def add_process(self, proc, data_dict):
        """ Add child process to list. """
        logger.info("Entered add_process. proc=%s data_dict=%s", proc, data_dict)
        self.proc_list.append(proc)
        self.rb_list.append(data_dict["rb_number"])

    def should_proceed(self, data_dict):
        """ Check whether there's a job already running with the same RB. """
        logger.info("ARP Entered should_proceed")
        if data_dict["rb_number"] in self.rb_list:
            logger.info("Duplicate RB run #%s, waiting for the first to finish.",
                        data_dict["rb_number"])
            return False
        # else return True
        return True

    @staticmethod
    def run_tuple(data_dict):
        """ return the tuple of (run_number, run version) from a dictionary. """
        logger.info("ARP Entered run_tuple")
        run_number = data_dict["run_number"]
        run_version = data_dict["run_version"] if data_dict["run_version"] is not None else 0
        return run_number, run_version

    def add_cancel(self, data_dict):
        """ Add this run to the cancel list, to cancel it next time it comes up. """
        logger.info("ARP Entered add_cancel")
        tup = self.run_tuple(data_dict)
        if tup not in self.cancel_list:
            self.cancel_list.append(tup)

    def should_cancel(self, data_dict):
        """ Return whether a run is in the list of runs to be canceled. """
        logger.info("ARP Entered should_cancel")
        tup = self.run_tuple(data_dict)
        return tup in self.cancel_list

    def cancel_run(self, data_dict):
        """ Cancel the reduction run. """
        logger.info("ARP Entered cancel_run")
        tup = self.run_tuple(data_dict)
        self.cancel_list.remove(tup)


class Consumer:
    # pylint: disable=too-few-public-methods
    """ Class used to setup the queue listener. """
    def __init__(self):
        """ Initialise consumer. """
        logger.info("ARP Entered Consumer.__init__")
        self.consumer_name = "autoreduction_processor"

    def run(self):
        """
        Connect to ActiveMQ via the QueueClient and listen to the
        /ReductionPending queue for messages.
        """
        logger.info("ARP Entered run")
        activemq_client = QueueClient()
        activemq_client.connect()
        activemq_client.subscribe_amq(consumer_name=self.consumer_name,
                                      listener=Listener())


def main():  # pragma: no cover
    """ Main method, starts consumer. """
    logger.info("ARP Entered main")
    logger.info("Start post process asynchronous listener!")
    # pylint: disable=maybe-no-member
    reactor.callWhenRunning(Consumer().run)
    reactor.run()
    logger.info("Stop post process asynchronous listener!")


if __name__ == '__main__':  # pragma: no cover
    main()
