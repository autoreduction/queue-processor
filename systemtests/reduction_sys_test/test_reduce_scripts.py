"""
This module is for testing the current reduction scripts and will notify on failure
"""
import time
from unittest import TestCase

import requests

from model.database import access as db
from queue_processors.queue_processor.settings import SCRIPT_TIMEOUT
from scripts.manual_operations import manual_submission

RUNS = [
    ("ARMI", 12345),
    ("TEST_INSTRUMENT", 143423)
]

class TestReduceScripts(TestCase):

    failures = []
    message = ""

    def tearDown(self) -> None:
        if self._is_test_failure():
            self._build_alert_message()
            self._alert_on_fail()

    def _is_test_failure(self):
        if hasattr(self, '_outcome'):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
            return len(result.failures) > 0 or len(result.errors) > 0
        return False

    def _build_alert_message(self):
        for fail in self.failures:
            self.message += f"\n - Reduction run {fail[1]} failed on instrument: {fail[0]} due to: {fail[2]}  "
        self.message += ""

    def _alert_on_fail(self):
        data = {
            "@context": "https://schema.org/extensions",
            "@type": "MessageCard",
            "themeColor": "0072C6",
            "title": "System Test Failure Alert",
            "text": f"Reductions failed on instruments:  \n{self.message}",
            "potentialAction": []
        }
        requests.post(os.environ.get("SYSTEST_WEBHOOK_URL"), json=data)

    def _is_run_complete(self):
        run = self._find_run_in_database()
        return run.status == db.get_status("e") or run.status == db.get_status("c")

    def _find_run_in_database(self):
        instrument = db.get_instrument(self.instrument)
        return instrument.reduction_runs.filter(run_number=self.run_number)

    def test_reduction(self):
        for run_pair in RUNS:
            with self.subTest():
                self.instrument = run_pair[0]
                self.run_number = run_pair[1]
                self.reason = ""

                try:
                    manual_submission.main(self.instrument, self.run_number)
                except:  # pylint:disable=bare-except
                    self.reason = "Failed to submit reduction run, ActiveMQ or ICAT may be unreachable"
                    self.fail(self.reason)
                start_time = time.time()
                while not self._is_run_complete():
                    time.sleep(1)
                    if time.time() - start_time > SCRIPT_TIMEOUT:
                        self.reason = "Reduction failed to complete within the timeout period"
                        self.fail(self.reason)

                run = self._find_run_in_database()

                self.reason = "Reduction run failed with error status"
                self.assertEqual(run.status,  db.get_status("c"), self.reason)
            if self._is_test_failure():
                TestReduceScripts.failures.append((self.instrument, self.run_number, self.reason))


