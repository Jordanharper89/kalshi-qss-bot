"""
Oracle Notification Worker

ORACLE-023.3

Purpose:
- Background worker that continuously processes
  Oracle notification queue.
"""

import threading
import time

from oracle_logger import oracle_logger


class OracleNotificationWorker:

    def __init__(
        self,
        dispatcher,
        interval_seconds=1,
    ):
        self.dispatcher = dispatcher
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
            "Oracle Notification Worker Started"
        )

    def stop(self):

        self._running = False

        oracle_logger.info(
            "Oracle Notification Worker Stopped"
        )

    def running(self):
        return self._running

    def _loop(self):

        while self._running:

            try:

                self.dispatcher.process()

            except Exception as error:

                oracle_logger.exception(error)

            time.sleep(
                self.interval_seconds
            )


oracle_notification_worker = None


def initialize_notification_worker(
    dispatcher,
    interval_seconds=1,
):

    global oracle_notification_worker

    oracle_notification_worker = OracleNotificationWorker(
        dispatcher,
        interval_seconds,
    )

    return oracle_notification_worker