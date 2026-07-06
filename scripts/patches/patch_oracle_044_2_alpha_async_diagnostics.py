from pathlib import Path
from datetime import datetime

path = Path("telegram_bot.py")

if not path.exists():
    raise FileNotFoundError("telegram_bot.py not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_suffix(f".py.bak_{stamp}")
backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

text = path.read_text(encoding="utf-8")

if "import traceback\n" not in text:
    text = text.replace("import time\n", "import time\nimport traceback\n")

old = '''def send_oracle_alpha_fast(chat_id):
    loading = send_message(
        chat_id,
        "⚡ ORACLE ALPHA DISCOVERY\\n\\nStatus:\\nBuilding live alpha feed...",
        reply_markup=oracle_feed_keyboard(),
    )

    message_id = None
    try:
        message_id = loading.get("result", {}).get("message_id")
    except Exception:
        pass

    def finish():
        msg = build_oracle_alpha_feed(limit=10)
        if message_id:
            edit_message(chat_id, message_id, msg, reply_markup=oracle_feed_keyboard())
        else:
            send_message(chat_id, msg, reply_markup=oracle_feed_keyboard())

    run_background(finish)


def edit_oracle_alpha_fast(chat_id, message_id):
    edit_message(
        chat_id,
        message_id,
        "⚡ ORACLE ALPHA DISCOVERY\\n\\nStatus:\\nRefreshing alpha feed...",
        reply_markup=oracle_feed_keyboard(),
    )

    def finish():
        edit_message(
            chat_id,
            message_id,
            build_oracle_alpha_feed(limit=10),
            reply_markup=oracle_feed_keyboard(),
        )

    run_background(finish)
'''

new = '''def send_oracle_alpha_fast(chat_id):
    print("[ORACLE-044.2] Alpha command received")

    loading = send_message(
        chat_id,
        "⚡ ORACLE ALPHA DISCOVERY\\n\\nStatus:\\nBuilding live alpha feed...",
        reply_markup=oracle_feed_keyboard(),
    )

    message_id = None
    try:
        message_id = loading.get("result", {}).get("message_id")
        print(f"[ORACLE-044.2] Loading message_id={message_id}")
    except Exception as e:
        print(f"[ORACLE-044.2] Could not read loading message id: {e}")

    def finish():
        started = time.time()
        print("[ORACLE-044.2] Alpha background started")

        try:
            print("[ORACLE-044.2] Building alpha feed...")
            msg = build_oracle_alpha_feed(limit=10)
            print(f"[ORACLE-044.2] Alpha feed built in {time.time() - started:.2f}s chars={len(str(msg))}")

            try:
                if message_id:
                    print("[ORACLE-044.2] Editing loading message with alpha feed...")
                    edit_message(chat_id, message_id, msg, reply_markup=oracle_feed_keyboard())
                    print("[ORACLE-044.2] Alpha edit queued")
                else:
                    print("[ORACLE-044.2] No message_id, sending new alpha message...")
                    send_message(chat_id, msg, reply_markup=oracle_feed_keyboard())
                    print("[ORACLE-044.2] Alpha send queued")

            except Exception as edit_error:
                print("[ORACLE-044.2] Alpha edit failed; sending fallback message")
                print(traceback.format_exc())
                send_message(
                    chat_id,
                    "⚡ ORACLE ALPHA DISCOVERY\\n\\nEdit failed, sending fresh result.\\n\\n" + str(msg),
                    reply_markup=oracle_feed_keyboard(),
                )

        except Exception as e:
            err = traceback.format_exc()
            print("[ORACLE-044.2] Alpha background failed")
            print(err)

            send_message(
                chat_id,
                f"⚡ ORACLE ALPHA DISCOVERY ERROR\\n\\n{e}",
                reply_markup=oracle_feed_keyboard(),
            )

    run_background(finish)


def edit_oracle_alpha_fast(chat_id, message_id):
    print(f"[ORACLE-044.2] Alpha callback received message_id={message_id}")

    edit_message(
        chat_id,
        message_id,
        "⚡ ORACLE ALPHA DISCOVERY\\n\\nStatus:\\nRefreshing alpha feed...",
        reply_markup=oracle_feed_keyboard(),
    )

    def finish():
        started = time.time()
        print("[ORACLE-044.2] Alpha callback background started")

        try:
            print("[ORACLE-044.2] Building callback alpha feed...")
            msg = build_oracle_alpha_feed(limit=10)
            print(f"[ORACLE-044.2] Callback alpha feed built in {time.time() - started:.2f}s chars={len(str(msg))}")

            try:
                edit_message(chat_id, message_id, msg, reply_markup=oracle_feed_keyboard())
                print("[ORACLE-044.2] Callback alpha edit queued")
            except Exception:
                print("[ORACLE-044.2] Callback alpha edit failed; sending fallback")
                print(traceback.format_exc())
                send_message(chat_id, msg, reply_markup=oracle_feed_keyboard())

        except Exception as e:
            print("[ORACLE-044.2] Callback alpha background failed")
            print(traceback.format_exc())
            send_message(
                chat_id,
                f"⚡ ORACLE ALPHA DISCOVERY ERROR\\n\\n{e}",
                reply_markup=oracle_feed_keyboard(),
            )

    run_background(finish)
'''

if old not in text:
    raise RuntimeError("Could not find alpha async helper block. Paste the current send_oracle_alpha_fast/edit_oracle_alpha_fast section.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")

print("===================================")
print(" ORACLE-044.2 INSTALLED")
print(" Alpha Async Diagnostics")
print("===================================")
print()
print(f"Backup created: {backup.name}")
print()
print("Test:")
print(" python telegram_bot.py")
print()
print("Telegram:")
print(" /oracle_alpha")
print()
print("Watch CMD for:")
print(" [ORACLE-044.2] Alpha background started")
print(" [ORACLE-044.2] Alpha feed built")
print(" [ORACLE-044.2] Alpha edit queued")