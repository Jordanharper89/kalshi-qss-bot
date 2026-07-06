"""
Oracle Notification Dispatcher

ORACLE-023.2

Purpose:
- Queue Oracle notifications.
- Prevent duplicate alerts.
- Rate-limit notifications.
- Deliver notifications through Notification Service.
"""

import time
from collections import deque


class OracleNotificationDispatcher:

    def __init__(
        self,
        notification_service,
        cooldown_seconds=30,
    ):
        self.notification_service = notification_service
        self.cooldown_seconds = cooldown_seconds

        self.queue = deque()
        self.last_sent = {}

    def queue_notification(
        self,
        notification_id,
        payload,
    ):
        self.queue.append(
            (
                notification_id,
                payload,
            )
        )

    def process(self):

        while self.queue:

            notification_id, payload = self.queue.popleft()

            now = time.time()

            previous = self.last_sent.get(
                notification_id,
                0,
            )

            if now - previous < self.cooldown_seconds:
                continue

            self.last_sent[
                notification_id
            ] = now

            if hasattr(
                self.notification_service,
                "send",
            ):
                self.notification_service.send(
                    payload
                )

            elif hasattr(
                self.notification_service,
                "notify",
            ):
                self.notification_service.notify(
                    payload
                )

    def clear(self):
        self.queue.clear()

    def size(self):
        return len(self.queue)