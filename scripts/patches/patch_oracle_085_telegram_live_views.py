from pathlib import Path
from datetime import datetime
import shutil

BOT = Path("telegram_bot.py")
VIEW = Path("oracle_telegram_live_views.py")

VIEW_CODE = r'''
"""
ORACLE-085 Telegram Live Views

Real short Oracle views for Telegram.
No giant 7,000 char cards.
"""

MAX_LEN = 3400


def trim(text):
    text = str(text or "")
    if len(text) <= MAX_LEN:
        return text
    return text[:MAX_LEN] + "\n\n⚠️ Trimmed for Telegram. Use CMD terminal for full output."


def oracle_live_summary():
    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()
        ranked = s.get("last_ranked") or []

        lines = [
            "🧠 ORACLE LIVE SUMMARY",
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

        return trim("\n".join(lines))
    except Exception as e:
        return f"ORACLE LIVE SUMMARY ERROR:\n{e}"


def oracle_alpha():
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

        return trim("\n".join(lines))
    except Exception as e:
        return f"ORACLE ALPHA ERROR:\n{e}"


def oracle_data_quality():
    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()
        dq = s.get("data_quality_planner_status") or {}
        return trim(dq.get("compact_card") or "No data-quality output yet.")
    except Exception as e:
        return f"DATA QUALITY ERROR:\n{e}"


def oracle_watchlist():
    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()
        ranked = s.get("last_ranked") or []

        lines = ["👁️ ORACLE WATCHLIST", ""]

        found = 0
        for x in ranked:
            action = x.get("oracle_final_action")
            if action in ("WATCH", "HUMAN_REVIEW", "READY_FOR_EXECUTION", "NO_TRADE"):
                found += 1
                lines += [
                    f"{found}. {x.get('ticker')}",
                    f"Action: {action} | Score: {x.get('oracle_final_score')}",
                    f"EV: {x.get('ev_decision')} | Gate: {x.get('execution_decision')}",
                    "",
                ]
            if found >= 8:
                break

        if found == 0:
            lines.append("No watchlist candidates yet.")

        return trim("\n".join(lines))
    except Exception as e:
        return f"WATCHLIST ERROR:\n{e}"


def oracle_signal_changes():
    try:
        import oracle_continuous_intelligence as o
        o.run_cycle()
        s = o.status()

        lines = [
            "🔮 SIGNAL CHANGES",
            "",
            f"Regime: {s.get('market_regime')}",
            f"Learning: {s.get('learning_final_router_status', {}).get('action_counts')}",
            f"Data Quality: {s.get('data_quality_feedback_status', {}).get('reason_counts')}",
            "",
            "This screen is now live, not placeholder.",
        ]

        return trim("\n".join(lines))
    except Exception as e:
        return f"SIGNAL CHANGE ERROR:\n{e}"


def oracle_intel():
    return oracle_live_summary()


def view_for_callback(data):
    data = str(data or "")

    if data in ("oracle_alpha", "oracle_feed"):
        return oracle_alpha()

    if data in ("oracle_intel", "oracle_core", "oracle_run", "oracle_dashboard"):
        return oracle_live_summary()

    if data in ("oracle_discovery", "oracle_data", "oracle_quality"):
        return oracle_data_quality()

    if data == "oracle_watchlist":
        return oracle_watchlist()

    if data == "oracle_signal_changes":
        return oracle_signal_changes()

    return None
'''

PATCH = r'''
# ORACLE-085 Telegram Live View Rescue
try:
    from oracle_telegram_live_views import view_for_callback as _oracle085_view_for_callback
except Exception:
    _oracle085_view_for_callback = None
'''

CALLBACK_PATCH = r'''
        # ORACLE-085 live view override
        try:
            if _oracle085_view_for_callback is not None:
                _oracle085_text = _oracle085_view_for_callback(data)
                if _oracle085_text:
                    edit_message_text(chat_id, message_id, _oracle085_text, reply_markup=oracle_menu_keyboard())
                    return
        except Exception as _oracle085_exc:
            edit_message_text(chat_id, message_id, f"ORACLE-085 live view error:\n{_oracle085_exc}")
            return
'''


def backup(path):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle085_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-085 INSTALLER")
    print(" Telegram Live Views Rescue")
    print("===================================")

    VIEW.write_text(VIEW_CODE, encoding="utf-8")
    print("[OK] Created oracle_telegram_live_views.py")

    if not BOT.exists():
        print("[FAIL] telegram_bot.py not found")
        return

    text = BOT.read_text(encoding="utf-8", errors="ignore")
    b = backup(BOT)

    if "ORACLE-085 Telegram Live View Rescue" not in text:
        # Insert import patch after imports
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines[:120]):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, PATCH)
        text = "\n".join(lines) + "\n"

    if "ORACLE-085 live view override" not in text:
        marker = "data = callback_query.get(\"data\")"
        if marker not in text:
            marker = "data = query.get(\"data\")"

        if marker in text:
            text = text.replace(marker, marker + "\n" + CALLBACK_PATCH, 1)
        else:
            print("[WARN] Could not find callback data marker. Created view file only.")

    BOT.write_text(text, encoding="utf-8")

    print("[OK] Patched telegram_bot.py")
    print(f"[OK] Backup created: {b}")

    print("")
    print("Tests:")
    print(" python -m py_compile telegram_bot.py")
    print(" python -c \"from oracle_telegram_live_views import oracle_alpha; print(oracle_alpha())\"")
    print(" python telegram_bot.py")
    print("")
    print("[DONE] ORACLE-085 installed")


if __name__ == "__main__":
    main()