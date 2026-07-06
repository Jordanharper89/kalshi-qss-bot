import os
import time
import queue
import threading
import traceback
from typing import Any, Dict, Optional, Tuple

import requests


TELEGRAM_QUEUE_ENABLED = os.getenv("KQ_TELEGRAM_QUEUE", "1").strip().lower() not in {"0", "false", "off", "no"}
TELEGRAM_QUEUE_MAXSIZE = int(os.getenv("KQ_TELEGRAM_QUEUE_MAXSIZE", "500"))
TELEGRAM_QUEUE_RETRIES = int(os.getenv("KQ_TELEGRAM_QUEUE_RETRIES", "2"))
TELEGRAM_QUEUE_RETRY_DELAY = float(os.getenv("KQ_TELEGRAM_QUEUE_RETRY_DELAY", "0.75"))
TELEGRAM_QUEUE_SLOW_SECONDS = float(os.getenv("KQ_TELEGRAM_QUEUE_SLOW_SECONDS", "1.0"))
TELEGRAM_QUEUE_DEFAULT_TIMEOUT = float(os.getenv("KQ_TELEGRAM_QUEUE_TIMEOUT", "6"))

_BASE_URL = None
_DIAG_FN = None
_STARTED = False
_WORKER_THREAD = None

_QUEUE = queue.Queue(maxsize=TELEGRAM_QUEUE_MAXSIZE)
_COUNTER = 0
_COUNTER_LOCK = threading.Lock()

_PENDING_LOCK = threading.Lock()
_LATEST_BY_TARGET: Dict[Tuple[str, str, str], int] = {}
_LAST_PAYLOAD_HASH: Dict[Tuple[str, str, str], str] = {}


class QueuedTelegramResponse:
    status_code = 202
    text = "QUEUED"

    def __init__(self, endpoint: str, request_id: int):
        self.endpoint = endpoint
        self.request_id = request_id

    def json(self):
        return {
            "ok": True,
            "queued": True,
            "endpoint": self.endpoint,
            "request_id": self.request_id,
        }


def _stamp() -> str:
    return time.strftime("%H:%M:%S")


def _diag(message: str) -> None:
    if _DIAG_FN:
        try:
            _DIAG_FN(message)
            return
        except Exception:
            pass
    print(f"[{_stamp()}] {message}", flush=True)


def _next_id() -> int:
    global _COUNTER
    with _COUNTER_LOCK:
        _COUNTER += 1
        return _COUNTER


def start_telegram_queue(base_url: str, diag_fn=None) -> None:
    global _BASE_URL, _DIAG_FN, _STARTED, _WORKER_THREAD

    _BASE_URL = str(base_url or "").rstrip("/")
    _DIAG_FN = diag_fn

    if not TELEGRAM_QUEUE_ENABLED:
        _diag("KQ-014 Telegram queue disabled by KQ_TELEGRAM_QUEUE=0")
        return

    if _STARTED:
        return

    _STARTED = True
    _WORKER_THREAD = threading.Thread(
        target=_worker_loop,
        daemon=True,
        name="telegram-queue-worker",
    )
    _WORKER_THREAD.start()
    _diag("KQ-014 Telegram queue started with coalescing")


def queue_size() -> int:
    try:
        return _QUEUE.qsize()
    except Exception:
        return 0


def _target_key(endpoint: str, payload: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
    if endpoint not in {"editMessageText", "editMessageReplyMarkup"}:
        return None

    chat_id = str(payload.get("chat_id", ""))
    message_id = str(payload.get("message_id", ""))

    if not chat_id or not message_id:
        return None

    return (endpoint, chat_id, message_id)


def _payload_hash(endpoint: str, payload: Dict[str, Any]) -> str:
    text = str(payload.get("text", ""))
    markup = str(payload.get("reply_markup", ""))
    return f"{endpoint}|{text}|{markup}"


def telegram_post(endpoint: str, payload: Dict[str, Any], timeout: Optional[float] = None, priority: str = "normal"):
    if not TELEGRAM_QUEUE_ENABLED:
        return telegram_post_sync(endpoint, payload, timeout=timeout)

    request_id = _next_id()
    target = _target_key(endpoint, payload)
    payload_sig = _payload_hash(endpoint, payload)

    if target:
        with _PENDING_LOCK:
            previous_id = _LATEST_BY_TARGET.get(target)
            previous_sig = _LAST_PAYLOAD_HASH.get(target)

            if previous_id is not None:
                action = "DUPLICATE" if previous_sig == payload_sig else "REPLACED"
                _diag(
                    f"TELEGRAM COALESCED {action} #{request_id} {endpoint} "
                    f"target={target[1]}:{target[2]} old=#{previous_id}"
                )

            _LATEST_BY_TARGET[target] = request_id
            _LAST_PAYLOAD_HASH[target] = payload_sig

    item = {
        "request_id": request_id,
        "endpoint": endpoint,
        "payload": payload,
        "timeout": timeout or TELEGRAM_QUEUE_DEFAULT_TIMEOUT,
        "created_at": time.perf_counter(),
        "priority": priority,
        "target": target,
        "payload_sig": payload_sig,
    }

    try:
        _QUEUE.put_nowait(item)
        _diag(f"TELEGRAM QUEUED #{request_id} {endpoint} queue={queue_size()}")
    except queue.Full:
        _diag(f"TELEGRAM QUEUE FULL - running sync #{request_id} {endpoint}")
        return telegram_post_sync(endpoint, payload, timeout=timeout)

    return QueuedTelegramResponse(endpoint, request_id)


def telegram_post_sync(endpoint: str, payload: Dict[str, Any], timeout: Optional[float] = None):
    if not _BASE_URL:
        raise RuntimeError("Telegram queue not initialized. Call start_telegram_queue(BASE) first.")

    timeout = timeout or TELEGRAM_QUEUE_DEFAULT_TIMEOUT
    start = time.perf_counter()
    response = requests.post(f"{_BASE_URL}/{endpoint}", json=payload, timeout=timeout)
    elapsed = time.perf_counter() - start
    status = getattr(response, "status_code", "?")

    if elapsed >= TELEGRAM_QUEUE_SLOW_SECONDS:
        _diag(f"SLOW TELEGRAM SYNC {endpoint}: {elapsed:.3f}s status={status}")
    else:
        _diag(f"Telegram sync {endpoint}: {elapsed:.3f}s status={status}")

    return response


def _worker_loop() -> None:
    while True:
        item = _QUEUE.get()
        try:
            if not _is_stale(item):
                _send_queued_item(item)
        except Exception:
            try:
                _diag(f"TELEGRAM QUEUE WORKER CRASH item={item.get('request_id')}")
            except Exception:
                _diag("TELEGRAM QUEUE WORKER CRASH")
            traceback.print_exc()
        finally:
            try:
                _QUEUE.task_done()
            except Exception:
                pass


def _is_stale(item: Dict[str, Any]) -> bool:
    target = item.get("target")
    if not target:
        return False

    request_id = item.get("request_id")

    with _PENDING_LOCK:
        latest_id = _LATEST_BY_TARGET.get(target)

    if latest_id != request_id:
        _diag(
            f"TELEGRAM SKIP STALE #{request_id} {item.get('endpoint')} "
            f"target={target[1]}:{target[2]} latest=#{latest_id}"
        )
        return True

    return False


def _clear_latest_if_current(item: Dict[str, Any]) -> None:
    target = item.get("target")
    if not target:
        return

    request_id = item.get("request_id")

    with _PENDING_LOCK:
        if _LATEST_BY_TARGET.get(target) == request_id:
            _LATEST_BY_TARGET.pop(target, None)
            _LAST_PAYLOAD_HASH.pop(target, None)


def _send_queued_item(item: Dict[str, Any]) -> None:
    request_id = item.get("request_id")
    endpoint = item.get("endpoint")
    payload = item.get("payload") or {}
    timeout = item.get("timeout") or TELEGRAM_QUEUE_DEFAULT_TIMEOUT
    wait_age = time.perf_counter() - item.get("created_at", time.perf_counter())

    last_error = None

    for attempt in range(1, TELEGRAM_QUEUE_RETRIES + 2):
        if _is_stale(item):
            return

        start = time.perf_counter()
        try:
            response = requests.post(f"{_BASE_URL}/{endpoint}", json=payload, timeout=timeout)
            elapsed = time.perf_counter() - start
            status = getattr(response, "status_code", "?")
            body_text = getattr(response, "text", "") or ""

            label = "SLOW TELEGRAM QUEUED" if elapsed >= TELEGRAM_QUEUE_SLOW_SECONDS else "Telegram queued"
            _diag(
                f"{label} #{request_id} {endpoint}: {elapsed:.3f}s status={status} "
                f"wait={wait_age:.3f}s queue={queue_size()} attempt={attempt}"
            )

            if status == 400:
                if "message is not modified" in body_text.lower():
                    _diag(f"TELEGRAM SKIP NOT MODIFIED #{request_id} {endpoint}")
                _clear_latest_if_current(item)
                return

            if status == 429 and attempt <= TELEGRAM_QUEUE_RETRIES + 1:
                retry_after = _extract_retry_after(response)
                time.sleep(retry_after or TELEGRAM_QUEUE_RETRY_DELAY)
                continue

            _clear_latest_if_current(item)
            return

        except Exception as e:
            elapsed = time.perf_counter() - start
            last_error = e
            _diag(
                f"TELEGRAM QUEUED FAILED #{request_id} {endpoint}: {elapsed:.3f}s "
                f"attempt={attempt} error={e}"
            )
            if attempt <= TELEGRAM_QUEUE_RETRIES + 1:
                time.sleep(TELEGRAM_QUEUE_RETRY_DELAY)

    if last_error:
        _diag(f"TELEGRAM QUEUED GAVE UP #{request_id} {endpoint}: {last_error}")

    _clear_latest_if_current(item)


def _extract_retry_after(response) -> Optional[float]:
    try:
        data = response.json()
        value = data.get("parameters", {}).get("retry_after")
        if value is not None:
            return float(value)
    except Exception:
        pass
    return None
