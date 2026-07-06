import time
from collections import deque
from threading import RLock

from services.base_service import BaseService
from services.trade_journal import trade_journal


class NotificationService(BaseService):
    def __init__(self):
        super().__init__("notification_service")
        self._lock = RLock()
        self._queue = deque()
        self.sent_count = 0
        self.queued_count = 0
        self.dropped_count = 0
        self.last_message = None
        self.last_error = None
        self.sender = None
        self.chat_id = None

    def start(self):
        self.mark_started()

    def stop(self):
        self.mark_stopped()

    def configure_sender(self, sender, chat_id=None):
        self.sender = sender
        self.chat_id = chat_id

    def notify(self, title, message, ticker=None, priority="normal", dedupe_key=None):
        item = {
            "time": int(time.time()),
            "title": str(title),
            "message": str(message),
            "ticker": str(ticker).upper().strip() if ticker else None,
            "priority": str(priority),
            "dedupe_key": dedupe_key,
        }

        with self._lock:
            if dedupe_key:
                for existing in self._queue:
                    if existing.get("dedupe_key") == dedupe_key:
                        self.dropped_count += 1
                        return False

            self._queue.append(item)
            self.queued_count += 1

        trade_journal.record_event("NOTIFICATION_QUEUED", ticker, item)
        return True

    def pending(self):
        with self._lock:
            return list(self._queue)

    def flush_one(self):
        with self._lock:
            if not self._queue:
                return None
            item = self._queue.popleft()

        try:
            text = f"{item['title']}\n\n{item['message']}"

            if self.sender:
                if self.chat_id is not None:
                    self.sender(self.chat_id, text)
                else:
                    self.sender(text)

            self.sent_count += 1
            self.last_message = item
            trade_journal.record_event("NOTIFICATION_SENT", item.get("ticker"), item)
            return item

        except Exception as e:
            self.last_error = str(e)

            with self._lock:
                self._queue.appendleft(item)

            trade_journal.record_event(
                "NOTIFICATION_FAILED",
                item.get("ticker"),
                {"error": str(e), "item": item},
            )
            return None

    def flush_all(self, limit=25):
        sent = []

        for _ in range(int(limit)):
            item = self.flush_one()
            if not item:
                break
            sent.append(item)

        return sent

    def diagnostics(self):
        data = super().diagnostics()

        with self._lock:
            queue_size = len(self._queue)

        data.update(
            {
                "queue_size": queue_size,
                "sent_count": self.sent_count,
                "queued_count": self.queued_count,
                "dropped_count": self.dropped_count,
                "last_error": self.last_error,
                "has_sender": self.sender is not None,
                "chat_id": self.chat_id,
            }
        )

        return data


notification_service = NotificationService()