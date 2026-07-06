
import os
import sys
import time
import html
import re
import traceback
import threading
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

WAITING_FOR = {}
SCAN_CACHE = {}
SCAN_CACHE_SECONDS = 5


def safe_import(name):
    try:
        return __import__(name, fromlist=["*"])
    except Exception:
        return None


def safe_call(label, fn, fallback="Unavailable"):
    try:
        return fn()
    except Exception as e:
        return f"{label} ERROR:\n{e}"


def short(text, limit=3900):
    text = str(text or "No output.")
    if len(text) <= limit:
        return text
    return text[: limit - 120] + "\n\n⚠️ Shortened for Telegram. Use CMD for full output."


def fmt(text):
    return html.escape(str(text or ""))


def post(endpoint, payload, timeout=10):
    return requests.post(f"{BASE}/{endpoint}", json=payload, timeout=timeout)


def send_message(chat_id, text, reply_markup=None):
    text = short(text)
    payload = {
        "chat_id": chat_id,
        "text": fmt(text),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        return post("sendMessage", payload, timeout=10).json()
    except Exception as e:
        print("Telegram send error:", e)
        return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    text = short(text)
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": fmt(text),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        return post("editMessageText", payload, timeout=10)
    except Exception as e:
        print("Telegram edit error:", e)
        return None


def answer_callback(callback_id, text="Updated"):
    try:
        requests.post(
            f"{BASE}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": text},
            timeout=2,
        )
    except Exception:
        pass


def run_background(fn, *args):
    t = threading.Thread(target=fn, args=args, daemon=True)
    t.start()
    return t


def run_script(args, timeout=180):
    try:
        result = subprocess.run(
            [sys.executable] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        out = result.stdout.strip()
        if result.stderr.strip():
            out += "\n\nERROR:\n" + result.stderr.strip()
        return short(out or "No output.")
    except Exception as e:
        return f"Command error:\n{e}"


def extract_ticker(text):
    raw = str(text or "").strip()

    if "op_market_ticker=" in raw:
        m = re.search(r"op_market_ticker=([^&\\s]+)", raw, re.I)
        if m:
            return m.group(1).strip().upper()

    if "kalshi.com" not in raw.lower():
        return raw.upper()

    raw = raw.split("?")[0].rstrip("/")
    for part in reversed(raw.split("/")):
        if "-" in part and any(c.isdigit() for c in part):
            return part.upper()

    return raw.upper()


def main_menu_text():
    return """Q SERIES COMMAND CENTER

/oracle = Oracle research
/oracle_feed = Oracle alpha feed
/check = Scan ticker/link
/positions = Open positions
/orders = Open orders
/settings = Trade settings
/balance = Account balance
/health = Runtime health
/help = Help
""".strip()


def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔮 Oracle AI", "callback_data": "oracle_menu"}],
            [{"text": "⚡ Oracle Feed", "callback_data": "oracle_feed"}],
            [{"text": "Scan Market", "callback_data": "main_check"}],
            [{"text": "Positions", "callback_data": "positions_main"}],
            [{"text": "Open Orders", "callback_data": "main_orders"}],
            [{"text": "Settings", "callback_data": "settings_main"}],
            [{"text": "Balance", "callback_data": "main_balance"}],
        ]
    }


def oracle_menu_text():
    return """🔮 ORACLE CONTROL CENTER

Live screens now show real engine output.

Use:
- Alpha Feed for discovered opportunities
- Intelligence for final decisions
- Data Quality for blockers
- Run Cycle to refresh Oracle
""".strip()


def oracle_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "⚡ Alpha Discovery", "callback_data": "oracle_alpha"}],
            [{"text": "🧠 Intelligence", "callback_data": "oracle_intel"}],
            [{"text": "🧰 Data Quality", "callback_data": "oracle_quality"}],
            [{"text": "👁 Watchlist", "callback_data": "oracle_watchlist"}],
            [{"text": "🔄 Run Oracle Cycle", "callback_data": "oracle_run"}],
            [{"text": "🏠 Home", "callback_data": "main_menu"}],
        ]
    }


def back_oracle_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "⬅ Back To Oracle", "callback_data": "oracle_menu"}],
            [{"text": "🏠 Home", "callback_data": "main_menu"}],
        ]
    }


def scan_keyboard(ticker):
    return {
        "inline_keyboard": [
            [
                {"text": "Buy YES $5", "callback_data": f"buy_live|{ticker}|YES|5"},
                {"text": "Buy NO $5", "callback_data": f"buy_live|{ticker}|NO|5"},
            ],
            [
                {"text": "Buy YES $10", "callback_data": f"buy_live|{ticker}|YES|10"},
                {"text": "Buy NO $10", "callback_data": f"buy_live|{ticker}|NO|10"},
            ],
            [{"text": "Full Scan", "callback_data": f"refresh_scan|{ticker}"}],
            [{"text": "Open Kalshi", "url": f"https://kalshi.com/markets/{ticker.lower()}"}],
            [{"text": "🏠 Home", "callback_data": "main_menu"}],
        ]
    }


def fast_scan_text(ticker):
    return f"""FAST TRADE CARD

Ticker:
{ticker}

Status:
READY

This is a quick action card.
Press Full Scan for deeper analysis.
""".strip()


def oracle_alpha_text():
    try:
        import oracle_cross_market_arbitrage as arb
        d = arb.diagnostics()
        top = d.get("top") or []

        lines = [
            "⚡ ORACLE ALPHA DISCOVERY",
            "",
            f"Raw Markets: {d.get('raw_markets')}",
            f"Tradable Markets: {d.get('tradable_markets')}",
            f"Alerts: {d.get('alerts')}",
            "",
            "Top Alpha:",
        ]

        for i, x in enumerate(top[:8], 1):
            lines += [
                "",
                f"#{i} {x.get('kind')}",
                f"Edge: {x.get('edge_pct')}%",
                f"Confidence: {x.get('confidence')}%",
                f"{x.get('recommendation')}",
            ]

        return "\n".join(lines)
    except Exception as e:
        return f"ORACLE ALPHA ERROR:\n{e}"


def oracle_intel_text():
    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()
        ranked = s.get("last_ranked") or []

        lines = [
            "🧠 ORACLE INTELLIGENCE",
            "",
            f"Regime: {s.get('market_regime')}",
            f"Final Actions: {s.get('final_decision_status', {}).get('action_counts')}",
            f"EV: {s.get('expected_value_status', {}).get('ev_counts')}",
            f"Queue: {s.get('execution_queue_status', {}).get('counts')}",
            "",
            "Top Opportunities:",
        ]

        for i, x in enumerate(ranked[:5], 1):
            lines += [
                "",
                f"#{i} {x.get('ticker')}",
                f"{x.get('title')}",
                f"Action: {x.get('oracle_final_action')}",
                f"Score: {x.get('oracle_final_score')}",
                f"Grade: {x.get('grade')}",
                f"Gate: {x.get('execution_decision')}",
                f"EV: {x.get('ev_decision')} | {x.get('ev_score')}",
                f"Tradability: {x.get('tradability')}",
                f"Order Book: {x.get('order_book_rating')}",
                f"Fill: {x.get('fill_probability')}",
            ]

        return "\n".join(lines)
    except Exception as e:
        return f"ORACLE INTEL ERROR:\n{e}"


def oracle_quality_text():
    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()
        dq = s.get("data_quality_planner_status") or {}
        return dq.get("compact_card") or "No data-quality output yet."
    except Exception as e:
        return f"ORACLE QUALITY ERROR:\n{e}"


def oracle_watchlist_text_live():
    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()
        ranked = s.get("last_ranked") or []
        lines = ["👁 ORACLE WATCHLIST", ""]

        for i, x in enumerate(ranked[:8], 1):
            lines += [
                f"{i}. {x.get('ticker')}",
                f"Action: {x.get('oracle_final_action')} | Score: {x.get('oracle_final_score')}",
                f"EV: {x.get('ev_decision')} | Gate: {x.get('execution_decision')}",
                "",
            ]

        return "\n".join(lines)
    except Exception as e:
        return f"WATCHLIST ERROR:\n{e}"


def health_text():
    lines = ["🧪 KQ / ORACLE HEALTH", ""]

    try:
        from oracle_market_cache import oracle_market_cache
        lines.append("Market Cache:")
        lines.append(str(oracle_market_cache.diagnostics()))
        lines.append("")
    except Exception as e:
        lines.append(f"Market Cache Error: {e}")

    try:
        import oracle_cross_market_arbitrage as arb
        lines.append("Arbitrage:")
        lines.append(str(arb.diagnostics()))
        lines.append("")
    except Exception as e:
        lines.append(f"Arbitrage Error: {e}")

    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()
        lines.append("Continuous Intelligence:")
        lines.append(f"Regime: {s.get('market_regime')}")
        lines.append(f"Final: {s.get('final_decision_status')}")
    except Exception as e:
        lines.append(f"Continuous Intelligence Error: {e}")

    return "\n".join(lines)


def positions_text():
    try:
        from position_cards import position_list_text
        return position_list_text()
    except Exception as e:
        return f"Positions unavailable:\n{e}"


def orders_text():
    try:
        from open_orders_panel import orders_panel_text
        return orders_panel_text()
    except Exception as e:
        return f"Orders unavailable:\n{e}"


def settings_text():
    try:
        from trade_settings import format_settings
        return format_settings()
    except Exception as e:
        return f"Settings unavailable:\n{e}"


def handle_command(chat_id, text):
    text = str(text or "").strip()

    if WAITING_FOR.get(chat_id) == "check":
        WAITING_FOR.pop(chat_id, None)
        ticker = extract_ticker(text)
        send_message(chat_id, fast_scan_text(ticker), reply_markup=scan_keyboard(ticker))
        return

    if text in ("/start", "/menu", "/help"):
        send_message(chat_id, main_menu_text(), reply_markup=main_menu_keyboard())
        return

    if text == "/oracle":
        send_message(chat_id, oracle_menu_text(), reply_markup=oracle_menu_keyboard())
        return

    if text in ("/oracle_feed", "/oracle_alpha", "/oracle_top"):
        send_message(chat_id, oracle_alpha_text(), reply_markup=back_oracle_keyboard())
        return

    if text in ("/oracle_intel", "/oracle_core"):
        send_message(chat_id, oracle_intel_text(), reply_markup=back_oracle_keyboard())
        return

    if text == "/oracle_quality":
        send_message(chat_id, oracle_quality_text(), reply_markup=back_oracle_keyboard())
        return

    if text == "/oracle_watchlist":
        send_message(chat_id, oracle_watchlist_text_live(), reply_markup=back_oracle_keyboard())
        return

    if text == "/health":
        send_message(chat_id, health_text(), reply_markup=main_menu_keyboard())
        return

    if text == "/positions":
        send_message(chat_id, positions_text(), reply_markup=main_menu_keyboard())
        return

    if text == "/orders":
        send_message(chat_id, orders_text(), reply_markup=main_menu_keyboard())
        return

    if text == "/settings":
        send_message(chat_id, settings_text(), reply_markup=main_menu_keyboard())
        return

    if text == "/balance":
        send_message(chat_id, run_script(["kalshi_auth.py"], timeout=90), reply_markup=main_menu_keyboard())
        return

    if text == "/check":
        WAITING_FOR[chat_id] = "check"
        send_message(chat_id, "Paste Kalshi link or ticker:")
        return

    if "kalshi.com" in text.lower() or text.upper().startswith("KX"):
        ticker = extract_ticker(text)
        send_message(chat_id, fast_scan_text(ticker), reply_markup=scan_keyboard(ticker))
        return

    send_message(chat_id, "Unknown command. Send /help", reply_markup=main_menu_keyboard())


def handle_callback(callback):
    callback_id = callback.get("id")
    data = callback.get("data", "")
    msg = callback.get("message", {})
    chat_id = str(msg.get("chat", {}).get("id"))
    message_id = msg.get("message_id")

    if CHAT_ID and chat_id != str(CHAT_ID):
        answer_callback(callback_id, "Not allowed")
        return

    answer_callback(callback_id, "Updated")

    if data == "main_menu":
        edit_message(chat_id, message_id, main_menu_text(), reply_markup=main_menu_keyboard())
        return

    if data == "oracle_menu":
        edit_message(chat_id, message_id, oracle_menu_text(), reply_markup=oracle_menu_keyboard())
        return

    if data in ("oracle_alpha", "oracle_feed", "oracle_top"):
        edit_message(chat_id, message_id, oracle_alpha_text(), reply_markup=back_oracle_keyboard())
        return

    if data in ("oracle_intel", "oracle_core", "oracle_dashboard"):
        edit_message(chat_id, message_id, oracle_intel_text(), reply_markup=back_oracle_keyboard())
        return

    if data in ("oracle_quality", "oracle_discovery"):
        edit_message(chat_id, message_id, oracle_quality_text(), reply_markup=back_oracle_keyboard())
        return

    if data == "oracle_watchlist":
        edit_message(chat_id, message_id, oracle_watchlist_text_live(), reply_markup=back_oracle_keyboard())
        return

    if data == "oracle_run":
        edit_message(chat_id, message_id, "🔄 Running Oracle cycle...", reply_markup=back_oracle_keyboard())

        def finish():
            edit_message(chat_id, message_id, oracle_intel_text(), reply_markup=back_oracle_keyboard())

        run_background(finish)
        return

    if data == "main_check":
        WAITING_FOR[chat_id] = "check"
        edit_message(chat_id, message_id, "Paste Kalshi link or ticker:")
        return

    if data == "positions_main":
        edit_message(chat_id, message_id, positions_text(), reply_markup=main_menu_keyboard())
        return

    if data == "main_orders":
        edit_message(chat_id, message_id, orders_text(), reply_markup=main_menu_keyboard())
        return

    if data == "settings_main":
        edit_message(chat_id, message_id, settings_text(), reply_markup=main_menu_keyboard())
        return

    if data == "main_balance":
        edit_message(chat_id, message_id, "Checking balance...", reply_markup=main_menu_keyboard())

        def finish():
            edit_message(chat_id, message_id, run_script(["kalshi_auth.py"], timeout=90), reply_markup=main_menu_keyboard())

        run_background(finish)
        return

    if data.startswith("refresh_scan|"):
        ticker = data.split("|", 1)[1]
        edit_message(chat_id, message_id, f"FULL SCAN\n\nTicker:\n{ticker}\n\nRunning...", reply_markup=scan_keyboard(ticker))

        def finish():
            edit_message(chat_id, message_id, run_script(["trade_scan.py", ticker], timeout=120), reply_markup=scan_keyboard(ticker))

        run_background(finish)
        return

    if data.startswith("buy_live|"):
        _, ticker, side, amount = data.split("|")
        edit_message(chat_id, message_id, f"BUY SUBMITTING\n\n{ticker}\n{side}\n${amount}")

        def finish():
            try:
                from kalshi_orders import place_live_buy_amount
                out = place_live_buy_amount(ticker, side, amount)
            except Exception as e:
                out = f"Buy unavailable/error:\n{e}"
            edit_message(chat_id, message_id, out, reply_markup=scan_keyboard(ticker))

        run_background(finish)
        return

    edit_message(chat_id, message_id, f"Unknown action:\n{data}", reply_markup=main_menu_keyboard())


def startup():
    print("Telegram bot running...")
    print("Send /help in Telegram.")
    print("KQ-021 clean Telegram bot active.")

    try:
        from services.service_manager import start_services
        start_services()
    except Exception as e:
        print(f"Service start skipped/error: {e}")

    try:
        import oracle_continuous_intelligence
        if hasattr(oracle_continuous_intelligence, "start"):
            oracle_continuous_intelligence.start(interval_seconds=10)
    except Exception as e:
        print(f"Oracle continuous start skipped/error: {e}")


def main():
    if not BOT_TOKEN:
        print("Missing TELEGRAM_BOT_TOKEN or BOT_TOKEN in .env")
        return

    startup()

    offset = None

    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset

            response = requests.get(f"{BASE}/getUpdates", params=params, timeout=40)
            data = response.json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                if "callback_query" in update:
                    handle_callback(update["callback_query"])
                    continue

                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id"))
                text = str(msg.get("text", "")).strip()

                if not text:
                    continue

                if CHAT_ID and chat_id != str(CHAT_ID):
                    continue

                handle_command(chat_id, text)

        except KeyboardInterrupt:
            print("Stopped.")
            break
        except Exception as e:
            print("Bot error:", e)
            traceback.print_exc()
            time.sleep(3)


if __name__ == "__main__":
    main()
