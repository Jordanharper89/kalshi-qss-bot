"""
Oracle Background Worker

ORACLE-023.1

Purpose:
- Runs Oracle continuously.
- Calls Oracle Engine.
- Sleeps between cycles.
- Safe start/stop.
"""

import threading
import time

from oracle_logger import oracle_logger


class OracleBackgroundWorker:

    def __init__(
        self,
        oracle_engine,
        interval_seconds=180,
    ):
        self.oracle_engine = oracle_engine
        self.interval_seconds = interval_seconds

        self._running = False
        self._thread = None

    def start(self):

        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
        )

        self._thread.start()

        oracle_logger.info(
            "Oracle Background Worker Started"
        )

    def stop(self):

        self._running = False

        oracle_logger.info(
            "Oracle Background Worker Stopped"
        )

    def running(self):
        return self._running

    def _loop(self):

        while self._running:

            try:

                self.oracle_engine.run()

            except Exception as error:

                oracle_logger.exception(error)

            time.sleep(
                self.interval_seconds
            )


oracle_background_worker = None


def initialize_background_worker(
    oracle_engine,
    interval_seconds=180,
):

    global oracle_background_worker

    oracle_background_worker = OracleBackgroundWorker(
        oracle_engine,
        interval_seconds,
    )

    return oracle_background_worker