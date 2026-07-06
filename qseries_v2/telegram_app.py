import time
import html
import traceback
import requests

from qseries_v2.config import BOT_TOKEN, CHAT_ID, BASE_URL
from qseries_v2.oracle_api import oracle_api
from qseries_v2.views import (
    home_text, home_keyboard, back_keyboard,
    format_play_list, format_snapshot, trim
)


def send(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": html.escape(trim(text)),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    return requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)


def edit(chat_id, message_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": html.escape(trim(text)),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    return requests.post(f"{BASE_URL}/editMessageText", json=payload, timeout=10)


def ack(callback_id, text="Updated"):
    try:
        requests.post(
            f"{BASE_URL}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": text},
            timeout=2,
        )
    except Exception:
        pass


def handle_command(chat_id, text):
    text = str(text or "").strip().lower()

    if text in ("/start", "/menu", "/help"):
        send(chat_id, home_text(), home_keyboard())
        return

    if text in ("/plays", "/live"):
        plays = oracle_api.get_live_plays("all")
        send(chat_id, format_play_list("🔥 LIVE PLAYS", plays), back_keyboard())
        return

    if text == "/sports":
        plays = oracle_api.get_live_plays("sports")
        send(chat_id, format_play_list("🏈 SPORTS PLAYS", plays), back_keyboard())
        return

    if text == "/weather":
        plays = oracle_api.get_live_plays("weather")
        send(chat_id, format_play_list("🌦 WEATHER PLAYS", plays), back_keyboard())
        return

    if text in ("/btc", "/bitcoin", "/crypto"):
        plays = oracle_api.get_live_plays("bitcoin")
        send(chat_id, format_play_list("₿ BITCOIN / CRYPTO PLAYS", plays), back_keyboard())
        return

    if text == "/snapshot":
        send(chat_id, format_snapshot(oracle_api.get_snapshot()), back_keyboard())
        return

    send(chat_id, home_text(), home_keyboard())


def handle_callback(callback):
    callback_id = callback.get("id")
    data = callback.get("data")
    msg = callback.get("message", {})
    chat_id = str(msg.get("chat", {}).get("id"))
    message_id = msg.get("message_id")

    ack(callback_id)

    if data == "home":
        edit(chat_id, message_id, home_text(), home_keyboard())
        return

    if data in ("live_plays", "plays_scalp", "plays_same_day", "plays_value"):
        plays = oracle_api.get_live_plays("all")
        title = {
            "live_plays": "🔥 LIVE PLAYS",
            "plays_scalp": "⚡ TOP SCALP PLAYS",
            "plays_same_day": "🎯 SAME-DAY PLAYS",
            "plays_value": "💎 TOP VALUE PLAYS",
        }.get(data, "🔥 LIVE PLAYS")
        edit(chat_id, message_id, format_play_list(title, plays), back_keyboard())
        return

    if data == "oracle_snapshot":
        edit(chat_id, message_id, format_snapshot(oracle_api.get_snapshot()), back_keyboard())
        return

    if data == "cat_sports":
        edit(chat_id, message_id, format_play_list("🏈 SPORTS PLAYS", oracle_api.get_live_plays("sports")), back_keyboard())
        return

    if data == "cat_weather":
        edit(chat_id, message_id, format_play_list("🌦 WEATHER PLAYS", oracle_api.get_live_plays("weather")), back_keyboard())
        return

    if data == "cat_bitcoin":
        edit(chat_id, message_id, format_play_list("₿ BITCOIN / CRYPTO PLAYS", oracle_api.get_live_plays("bitcoin")), back_keyboard())
        return

    edit(chat_id, message_id, home_text(), home_keyboard())


def run_bot():
    if not BOT_TOKEN:
        print("Missing TELEGRAM_BOT_TOKEN or BOT_TOKEN in .env")
        return

    print("Q Series V2 running.")
    print("Send /menu in Telegram.")

    offset = None

    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset

            data = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=40).json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                if "callback_query" in update:
                    handle_callback(update["callback_query"])
                    continue

                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id"))
                text = str(msg.get("text", "")).strip()

                if CHAT_ID and chat_id != str(CHAT_ID):
                    continue

                if text:
                    handle_command(chat_id, text)

        except KeyboardInterrupt:
            print("Stopped.")
            break
        except Exception as e:
            print("Bot error:", e)
            traceback.print_exc()
            time.sleep(3)
