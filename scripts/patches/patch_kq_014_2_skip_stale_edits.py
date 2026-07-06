from pathlib import Path

bot_file = Path("telegram_bot.py")

if not bot_file.exists():
    print("[ERROR] telegram_bot.py not found")
    raise SystemExit

text = bot_file.read_text(encoding="utf-8")

backup = Path("telegram_bot.py.kq0142_backup")
backup.write_text(text, encoding="utf-8")
print("[OK] Backup saved:", backup)

patch_code = r'''

# ==============================
# KQ-014.2 SKIP STALE TELEGRAM EDITS
# ==============================

telegram_latest_edit_serial = {}
telegram_latest_edit_lock = threading.Lock()

_original_telegram_queue_request = None

try:
    _original_telegram_queue_request = telegram_queue_request
except NameError:
    _original_telegram_queue_request = None


def kq0142_target_key(method, payload):
    try:
        if method not in ("editMessageText", "editMessageReplyMarkup"):
            return None

        chat_id = payload.get("chat_id")
        message_id = payload.get("message_id")

        if chat_id is None or message_id is None:
            return None

        return f"{chat_id}:{message_id}"
    except Exception:
        return None


def telegram_queue_request(method, payload):
    if _original_telegram_queue_request is None:
        print("[KQ-014.2] original telegram_queue_request not found")
        return None

    key = kq0142_target_key(method, payload)

    if key:
        with telegram_latest_edit_lock:
            old_serial = telegram_latest_edit_serial.get(key, 0)
            new_serial = old_serial + 1
            telegram_latest_edit_serial[key] = new_serial

        payload["_kq0142_target_key"] = key
        payload["_kq0142_serial"] = new_serial

    return _original_telegram_queue_request(method, payload)


try:
    _original_telegram_worker_send = telegram_worker_send
except NameError:
    _original_telegram_worker_send = None


def telegram_worker_send(method, payload):
    if _original_telegram_worker_send is None:
        print("[KQ-014.2] original telegram_worker_send not found")
        return None

    key = payload.get("_kq0142_target_key")
    serial = payload.get("_kq0142_serial")

    if key and serial:
        with telegram_latest_edit_lock:
            latest = telegram_latest_edit_serial.get(key)

        if latest != serial:
            print(
                f"[KQ-014.2] SKIP STALE {method} "
                f"target={key} serial={serial} latest={latest}"
            )
            return None

    return _original_telegram_worker_send(method, payload)

print("[KQ-014.2] stale Telegram edit protection loaded")
'''

if "KQ-014.2 SKIP STALE TELEGRAM EDITS" in text:
    print("[SKIP] KQ-014.2 already installed")
else:
    text += patch_code
    bot_file.write_text(text, encoding="utf-8")
    print("[DONE] KQ-014.2 patch added")