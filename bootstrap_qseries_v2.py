from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"

FILES = {
    "config.py": r'''
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
''',

    "play_model.py": r'''
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class Play:
    ticker: str
    title: str
    category: str = "UNKNOWN"
    play_type: str = "VALUE"
    mission: str = "WATCH"
    side: str = "WATCH"
    current_price: float = 0.0
    fair_value: float = 0.0
    edge: float = 0.0
    confidence: float = 0.0
    grade: str = "UNRATED"
    source: str = "ORACLE"
    reason: str = ""

    def to_dict(self):
        d = asdict(self)
        d["timestamp"] = datetime.now(timezone.utc).isoformat()
        return d
''',

    "oracle_api.py": r'''
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.play_model import Play


class OracleAPI:
    def get_alpha_plays(self, limit=10):
        plays = []
        try:
            import oracle_cross_market_arbitrage as arb
            d = arb.diagnostics()
            for item in (d.get("top") or [])[:limit]:
                edge_pct = float(item.get("edge_pct") or 0)
                confidence = float(item.get("confidence") or 0)
                kind = str(item.get("kind") or "alpha")

                plays.append(Play(
                    ticker=f"ORACLE-{kind.upper()}",
                    title=kind.replace("_", " ").title(),
                    category="ORACLE",
                    play_type="ALPHA",
                    mission="WATCH",
                    side="WATCH",
                    edge=edge_pct,
                    confidence=confidence,
                    grade=self._grade(edge_pct, confidence),
                    reason=item.get("recommendation") or "",
                ).to_dict())
        except Exception as e:
            plays.append(Play(
                ticker="ORACLE-ERROR",
                title="Oracle Alpha Error",
                mission="IGNORE",
                reason=str(e),
            ).to_dict())
        return plays

    def get_live_plays(self, category="all", limit=10):
        if category in ("oracle", "all"):
            return self.get_alpha_plays(limit=limit)

        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "category_scan.py", category],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=240,
                errors="replace",
            )
            text = (result.stdout or result.stderr or "").strip()
            return [Play(
                ticker=f"{category.upper()}-SCAN",
                title=f"{category.title()} Scan Output",
                category=category.upper(),
                mission="REVIEW",
                reason=text[:2500] if text else "No output.",
            ).to_dict()]
        except Exception as e:
            return [Play(
                ticker=f"{category.upper()}-ERROR",
                title=f"{category.title()} Scan Error",
                category=category.upper(),
                mission="IGNORE",
                reason=str(e),
            ).to_dict()]

    def get_snapshot(self):
        try:
            import oracle_continuous_intelligence as o
            o.run_cycle()
            s = o.status()
            return {
                "status": "ok",
                "market_regime": s.get("market_regime"),
                "final_decision_status": s.get("final_decision_status"),
                "data_quality": s.get("data_quality_planner_status", {}).get("status"),
                "ranked_count": len(s.get("last_ranked") or []),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _grade(self, edge, confidence):
        score = edge + confidence / 10
        if score >= 30:
            return "A+"
        if score >= 20:
            return "A"
        if score >= 12:
            return "B"
        return "WATCH"


oracle_api = OracleAPI()
''',

    "views.py": r'''
def trim(text, limit=3900):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[:limit - 80] + "\n\n...shortened..."


def home_text():
    return """🏠 Q SERIES V2

Oracle finds the Plays.
Q Series executes the Plays.

Choose a section:"""


def home_keyboard():
    return {"inline_keyboard": [
        [{"text": "🔥 Live Plays", "callback_data": "live_plays"}],
        [{"text": "⚡ Top Scalp Plays", "callback_data": "plays_scalp"}],
        [{"text": "🎯 Same-Day Plays", "callback_data": "plays_same_day"}],
        [{"text": "💎 Top Value Plays", "callback_data": "plays_value"}],
        [{"text": "🧠 Oracle Snapshot", "callback_data": "oracle_snapshot"}],
        [{"text": "🏈 Sports", "callback_data": "cat_sports"}],
        [{"text": "🌦 Weather", "callback_data": "cat_weather"}],
        [{"text": "₿ Bitcoin / Crypto", "callback_data": "cat_bitcoin"}],
    ]}


def back_keyboard():
    return {"inline_keyboard": [[{"text": "🏠 Home", "callback_data": "home"}]]}


def format_play_card(play):
    return f"""🔥 PLAY CARD

Mission: {play.get('mission')}
Ticker: {play.get('ticker')}
Market: {play.get('title')}

Category: {play.get('category')}
Type: {play.get('play_type')}
Side: {play.get('side')}

Edge: {play.get('edge')}
Confidence: {play.get('confidence')}%
Grade: {play.get('grade')}

Reason:
{play.get('reason')}
""".strip()


def format_play_list(title, plays):
    lines = [title, ""]
    if not plays:
        lines.append("No Plays found.")
        return "\n".join(lines)

    for i, p in enumerate(plays, 1):
        lines.append(f"{i}. {p.get('mission')} | {p.get('ticker')}")
        lines.append(f"   {p.get('title')}")
        lines.append(f"   Edge: {p.get('edge')} | Conf: {p.get('confidence')} | Grade: {p.get('grade')}")
        if p.get("reason"):
            lines.append(f"   {str(p.get('reason'))[:180]}")
        lines.append("")
    return trim("\n".join(lines))


def format_snapshot(snapshot):
    lines = ["🧠 ORACLE SNAPSHOT", ""]
    for k, v in snapshot.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)
''',

    "telegram_app.py": r'''
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
''',

    "main.py": r'''
from qseries_v2.telegram_app import run_bot

if __name__ == "__main__":
    run_bot()
''',
}


def main():
    print("===================================")
    print(" KQ-V2.0 BOOTSTRAP")
    print("===================================")

    BASE.mkdir(exist_ok=True)
    (BASE / "scanners").mkdir(exist_ok=True)
    (BASE / "oracle").mkdir(exist_ok=True)
    (BASE / "state").mkdir(exist_ok=True)

    for rel, code in FILES.items():
        path = BASE / rel
        path.write_text(code.strip() + "\n", encoding="utf-8")
        print(f"[OK] Created {path}")

    (BASE / "__init__.py").write_text("", encoding="utf-8")
    print("[OK] Created qseries_v2 package")

    print("")
    print("Run tests:")
    print(" python -m py_compile qseries_v2\\main.py qseries_v2\\telegram_app.py qseries_v2\\oracle_api.py qseries_v2\\views.py")
    print(" python qseries_v2\\main.py")
    print("")
    print("[DONE] KQ-V2.0 bootstrap complete")


if __name__ == "__main__":
    main()