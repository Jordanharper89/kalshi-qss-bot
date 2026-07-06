"""
ORACLE-038.2 — Oracle Controller

Purpose:
- Centralize Oracle command/callback routing
- Keep telegram_bot.py from becoming overloaded with Oracle-specific logic
- Provide one clean controller interface for future Oracle screens

Safe module:
- Does not execute trades
- Does not place orders
- UI/controller only
"""

from oracle_dashboard_ui import (
    oracle_dashboard_text,
    oracle_dashboard_keyboard,
    oracle_premium_home_text,
    oracle_premium_home_keyboard,
)

from oracle_event_alert_ui import (
    recent_event_alerts_text,
    event_alert_keyboard,
)

import oracle_core
import oracle_continuous_intelligence


def oracle_back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "⬅ Back To Oracle", "callback_data": "oracle_menu"}],
            [{"text": "🏠 Main Menu", "callback_data": "main_menu"}],
        ]
    }


def build_oracle_dashboard_snapshot():
    """
    Controller-local lightweight dashboard snapshot.
    This mirrors the safe dashboard snapshot logic from telegram_bot.py.
    """
    snapshot = {
        "health": {
            "healthy": True,
        },
        "scheduler": {
            "running": True,
            "cycles_completed": 0,
            "last_cycle": "Controller mode",
        },
        "metrics": {
            "total_cycles": 0,
            "markets_scanned": 0,
            "markets_researched": 0,
            "signal_changes": 0,
        },
        "opportunity_feed": [],
        "recent_alerts": [],
        "alert_statistics": {
            "total_alerts": 0,
        },
    }

    try:
        import json
        from pathlib import Path

        watch_file = Path("oracle_watchlist.json")
        if watch_file.exists():
            data = json.loads(watch_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                snapshot["metrics"]["markets_researched"] = len(data)
            elif isinstance(data, dict):
                snapshot["metrics"]["markets_researched"] = len(data)

        alert_file = Path("oracle_alert_history.json")
        if alert_file.exists():
            alerts = json.loads(alert_file.read_text(encoding="utf-8"))
            if isinstance(alerts, list):
                snapshot["recent_alerts"] = alerts[:10]
                snapshot["alert_statistics"]["total_alerts"] = len(alerts)

    except Exception:
        snapshot["health"]["healthy"] = False

    return snapshot


def oracle_placeholder_text(title):
    return f"""
━━━━━━━━━━━━━━━━━━━━━━
🔮 {title}
━━━━━━━━━━━━━━━━━━━━━━

Status:
This Oracle screen is connected through Oracle Controller.

━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def command_names():
    return {
        "/oracle",
        "/oracle_dashboard",
        "/oracle_events",
        "/oracle_intel",
        "/oracle_core",
    }


def callback_prefixes():
    return {
        "oracle_menu",
        "oracle_dashboard",
        "oracle_events",
        "oracle_events_high",
        "oracle_events_medium",
        "oracle_events_low",
        "oracle_intel",
        "oracle_core",
        "oracle_health",
        "oracle_metrics",
        "oracle_discovery",
        "oracle_signal_changes",
    }


def is_oracle_command(text):
    return str(text or "").strip().split(" ")[0] in command_names()


def is_oracle_callback(data):
    return str(data or "") in callback_prefixes()


def handle_command(text):
    """
    Returns:
    {
        handled: bool,
        text: str,
        reply_markup: dict
    }
    """
    text = str(text or "").strip()

    if text == "/oracle":
        return {
            "handled": True,
            "text": oracle_premium_home_text(),
            "reply_markup": oracle_premium_home_keyboard(),
        }

    if text == "/oracle_dashboard":
        snapshot = build_oracle_dashboard_snapshot()
        return {
            "handled": True,
            "text": oracle_dashboard_text(snapshot),
            "reply_markup": oracle_dashboard_keyboard(),
        }

    if text == "/oracle_events":
        return {
            "handled": True,
            "text": recent_event_alerts_text(limit=10),
            "reply_markup": event_alert_keyboard(),
        }

    if text == "/oracle_intel":
        return {
            "handled": True,
            "text": oracle_continuous_intelligence.format_status(),
            "reply_markup": oracle_back_keyboard(),
        }

    if text == "/oracle_core":
        return {
            "handled": True,
            "text": oracle_core.format_status(),
            "reply_markup": oracle_back_keyboard(),
        }

    return {
        "handled": False,
    }


def handle_callback(data):
    """
    Returns:
    {
        handled: bool,
        answer: str,
        text: str,
        reply_markup: dict
    }
    """
    data = str(data or "")

    if data == "oracle_menu":
        return {
            "handled": True,
            "answer": "Oracle",
            "text": oracle_premium_home_text(),
            "reply_markup": oracle_premium_home_keyboard(),
        }

    if data == "oracle_dashboard":
        snapshot = build_oracle_dashboard_snapshot()
        return {
            "handled": True,
            "answer": "Dashboard",
            "text": oracle_dashboard_text(snapshot),
            "reply_markup": oracle_dashboard_keyboard(),
        }

    if data == "oracle_events":
        return {
            "handled": True,
            "answer": "Events",
            "text": recent_event_alerts_text(limit=10),
            "reply_markup": event_alert_keyboard(),
        }

    if data == "oracle_events_high":
        return {
            "handled": True,
            "answer": "High events",
            "text": recent_event_alerts_text(limit=10, priority="HIGH"),
            "reply_markup": event_alert_keyboard(),
        }

    if data == "oracle_events_medium":
        return {
            "handled": True,
            "answer": "Medium events",
            "text": recent_event_alerts_text(limit=10, priority="MEDIUM"),
            "reply_markup": event_alert_keyboard(),
        }

    if data == "oracle_events_low":
        return {
            "handled": True,
            "answer": "Low events",
            "text": recent_event_alerts_text(limit=10, priority="LOW"),
            "reply_markup": event_alert_keyboard(),
        }

    if data == "oracle_intel":
        return {
            "handled": True,
            "answer": "Intel",
            "text": oracle_continuous_intelligence.format_status(),
            "reply_markup": oracle_back_keyboard(),
        }

    if data == "oracle_core":
        return {
            "handled": True,
            "answer": "Core",
            "text": oracle_core.format_status(),
            "reply_markup": oracle_back_keyboard(),
        }

    if data == "oracle_health":
        snapshot = build_oracle_dashboard_snapshot()
        health = snapshot.get("health", {})
        return {
            "handled": True,
            "answer": "Health",
            "text": f"""
❤️ ORACLE HEALTH

Healthy:
{health.get("healthy")}

Status:
Oracle Controller is connected.
""".strip(),
            "reply_markup": oracle_back_keyboard(),
        }

    if data == "oracle_metrics":
        snapshot = build_oracle_dashboard_snapshot()
        metrics = snapshot.get("metrics", {})
        return {
            "handled": True,
            "answer": "Metrics",
            "text": f"""
📈 ORACLE METRICS

Research Cycles:
{metrics.get("total_cycles", 0)}

Markets Scanned:
{metrics.get("markets_scanned", 0)}

Markets Researched:
{metrics.get("markets_researched", 0)}

Signal Changes:
{metrics.get("signal_changes", 0)}
""".strip(),
            "reply_markup": oracle_back_keyboard(),
        }

    if data == "oracle_discovery":
        return {
            "handled": True,
            "answer": "Discovery",
            "text": oracle_placeholder_text("MARKET DISCOVERY"),
            "reply_markup": oracle_back_keyboard(),
        }

    if data == "oracle_signal_changes":
        return {
            "handled": True,
            "answer": "Signal Changes",
            "text": oracle_placeholder_text("SIGNAL CHANGES"),
            "reply_markup": oracle_back_keyboard(),
        }

    return {
        "handled": False,
    }


def diagnostics():
    return {
        "module": "oracle_controller",
        "status": "ok",
        "commands": sorted(command_names()),
        "callbacks": sorted(callback_prefixes()),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(diagnostics(), indent=2))
