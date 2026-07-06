from pathlib import Path
from datetime import datetime
import shutil

BOT = Path("telegram_bot.py")
GUARD = Path("telegram_text_guard.py")
RESCUE = Path("kq_scan_rescue.py")

GUARD_CODE = r'''
"""
KQ-020 Telegram Text Guard

Prevents Telegram edit/send failures caused by oversized messages.
Telegram text limit is roughly 4096 chars, so we cap at 3900.
"""

MAX_TEXT = 3900
_INSTALLED = False


def _shorten(text):
    text = str(text or "")
    if len(text) <= MAX_TEXT:
        return text
    footer = "\n\n⚠️ Message shortened by KQ-020 Telegram guard.\nUse CMD terminal for full output."
    return text[: MAX_TEXT - len(footer)] + footer


def install():
    global _INSTALLED
    if _INSTALLED:
        return

    try:
        import requests
    except Exception:
        return

    original_post = requests.post

    def guarded_post(url, *args, **kwargs):
        try:
            data = kwargs.get("data")
            js = kwargs.get("json")

            target = str(url or "")
            is_telegram_text = (
                "api.telegram.org" in target
                and (
                    "sendMessage" in target
                    or "editMessageText" in target
                    or "sendPhoto" in target
                    or "editMessageCaption" in target
                )
            )

            if is_telegram_text:
                if isinstance(js, dict):
                    if "text" in js:
                        js["text"] = _shorten(js.get("text"))
                    if "caption" in js:
                        js["caption"] = _shorten(js.get("caption"))
                    kwargs["json"] = js

                if isinstance(data, dict):
                    if "text" in data:
                        data["text"] = _shorten(data.get("text"))
                    if "caption" in data:
                        data["caption"] = _shorten(data.get("caption"))
                    kwargs["data"] = data

        except Exception:
            pass

        return original_post(url, *args, **kwargs)

    requests.post = guarded_post
    _INSTALLED = True
'''

RESCUE_CODE = r'''
"""
KQ-020 Scan Rescue

Run:
 python kq_scan_rescue.py

Purpose:
- Show whether Oracle/KQ is actually producing scan candidates.
- Show whether market data service is making API calls.
- Show top blockers.
"""

import importlib
import traceback


def safe_import(name):
    try:
        return importlib.import_module(name)
    except Exception as exc:
        return exc


def print_block(title):
    print("")
    print("=" * 60)
    print(title)
    print("=" * 60)


def main():
    print_block("KQ-020 SCAN RESCUE")

    # Oracle continuous intelligence
    print_block("ORACLE CONTINUOUS INTELLIGENCE")
    o = safe_import("oracle_continuous_intelligence")
    if isinstance(o, Exception):
        print("[FAIL] Cannot import oracle_continuous_intelligence")
        print(o)
    else:
        try:
            if hasattr(o, "run_cycle"):
                o.run_cycle()
            s = o.status() if hasattr(o, "status") else {}
            ranked = s.get("last_ranked") or []

            print(f"ranked_count: {len(ranked)}")
            print(f"market_regime: {s.get('market_regime')}")
            print(f"final_decision_status: {s.get('final_decision_status')}")
            print(f"execution_queue_status: {s.get('execution_queue_status')}")
            print(f"data_quality_status: {s.get('data_quality_planner_status', {}).get('status')}")

            if ranked:
                top = ranked[0]
                print("")
                print("TOP OPPORTUNITY")
                print(f"ticker: {top.get('ticker')}")
                print(f"title: {top.get('title')}")
                print(f"grade: {top.get('grade')}")
                print(f"execution_decision: {top.get('execution_decision')}")
                print(f"oracle_final_action: {top.get('oracle_final_action')}")
                print(f"tradability: {top.get('tradability')}")
                print(f"order_book_rating: {top.get('order_book_rating')}")
                print(f"fill_probability: {top.get('fill_probability')}")
                print(f"reason_type: {top.get('oracle_no_trade_reason_type')}")
            else:
                print("[WARN] Oracle returned ZERO ranked opportunities.")
        except Exception:
            traceback.print_exc()

    # Common services/modules
    print_block("SERVICE / MARKET DATA CHECKS")
    candidates = [
        "market_data_service",
        "kalshi_market_data",
        "kalshi_client",
        "oracle_market_cache",
        "oracle_research_engine",
        "oracle_cross_market_arbitrage",
        "oracle_market_loader",
    ]

    for name in candidates:
        mod = safe_import(name)
        if isinstance(mod, Exception):
            print(f"[MISS] {name}: {mod}")
            continue

        print(f"[OK] import {name}")

        for attr in ["diagnostics", "status", "get_status"]:
            fn = getattr(mod, attr, None)
            if callable(fn):
                try:
                    print(f"{name}.{attr}(): {fn()}")
                except Exception as exc:
                    print(f"{name}.{attr}() error: {exc}")

        for obj_name in [
            "oracle_market_cache",
            "oracle_research_engine",
            "oracle_cross_market_arbitrage",
            "market_data_service",
        ]:
            obj = getattr(mod, obj_name, None)
            if obj:
                for attr in ["diagnostics", "status", "get_status"]:
                    fn = getattr(obj, attr, None)
                    if callable(fn):
                        try:
                            print(f"{name}.{obj_name}.{attr}(): {fn()}")
                        except Exception as exc:
                            print(f"{name}.{obj_name}.{attr}() error: {exc}")

    print_block("WHAT THIS MEANS")
    print("If market_data shows registered_tickers=0 and api_calls=0, the bot is running but no real scan universe is being registered.")
    print("If Oracle ranked_count > 0 but final_action is NO_TRADE, Oracle is scanning but blocking candidates.")
    print("If Telegram status=400 happens after long cards, the Telegram guard should stop oversized edit failures.")

    print("")
    print("[DONE] KQ-020 scan rescue complete")


if __name__ == "__main__":
    main()
'''


def backup(path):
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_kq020_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" KQ-020 INSTALLER")
    print(" Scan Rescue + Telegram Hardening")
    print("===================================")

    GUARD.write_text(GUARD_CODE, encoding="utf-8")
    RESCUE.write_text(RESCUE_CODE, encoding="utf-8")
    print("[OK] Created telegram_text_guard.py")
    print("[OK] Created kq_scan_rescue.py")

    if not BOT.exists():
        print("[WARN] telegram_bot.py not found. Bot hardening skipped.")
    else:
        text = BOT.read_text(encoding="utf-8", errors="ignore")

        if "KQ-020 Telegram Text Guard" in text:
            print("[SKIP] telegram_bot.py already patched")
        else:
            b = backup(BOT)

            install_block = '''
# KQ-020 Telegram Text Guard
try:
    from telegram_text_guard import install as _kq020_install_telegram_guard
    _kq020_install_telegram_guard()
    print("[KQ-020] Telegram Text Guard active")
except Exception as _kq020_exc:
    print(f"[KQ-020] Telegram Text Guard failed: {_kq020_exc}")
'''

            # Put it after imports if possible, otherwise top of file.
            lines = text.splitlines()
            insert_at = 0
            for i, line in enumerate(lines[:80]):
                if line.startswith("import ") or line.startswith("from "):
                    insert_at = i + 1

            lines.insert(insert_at, install_block)
            BOT.write_text("\n".join(lines) + "\n", encoding="utf-8")

            print("[OK] Patched telegram_bot.py")
            print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python kq_scan_rescue.py")
    print(" python telegram_bot.py")
    print("")
    print("[DONE] KQ-020 installed")


if __name__ == "__main__":
    main()