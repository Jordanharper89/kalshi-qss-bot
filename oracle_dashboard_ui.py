"""
Oracle Dashboard UI

ORACLE-024.1

Purpose:
- Premium Telegram dashboard formatting for Oracle.
- Emoji-rich mobile layout.
- No Telegram sending.
- No trade execution.
"""


def oracle_dashboard_text(snapshot):
    snapshot = snapshot or {}

    health = snapshot.get("health") or {}
    metrics = snapshot.get("metrics") or {}
    scheduler = snapshot.get("scheduler") or {}
    feed = snapshot.get("opportunity_feed") or []
    alerts = snapshot.get("recent_alerts") or []
    alert_stats = snapshot.get("alert_statistics") or {}

    healthy = health.get("healthy", False)
    status_icon = "🟢" if healthy else "🔴"
    status_text = "ONLINE" if healthy else "NEEDS CHECK"

    scheduler_running = scheduler.get("running", False)
    scheduler_icon = "🟢" if scheduler_running else "🟡"
    scheduler_text = "RUNNING" if scheduler_running else "PAUSED"

    return f"""
━━━━━━━━━━━━━━━━━━━━━━
🔮 ORACLE AI DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━

{status_icon} Status:
{status_text}

{scheduler_icon} Scheduler:
{scheduler_text}

🌎 Markets Scanned:
{metrics.get("markets_scanned", 0)}

🧠 Research Cycles:
{metrics.get("total_cycles", 0)}

👀 Markets Researched:
{metrics.get("markets_researched", 0)}

📊 Live Opportunities:
{len(feed)}

🚨 Recent Alerts:
{len(alerts)}

⚡ Signal Changes:
{metrics.get("signal_changes", 0)}

📣 Total Alerts:
{alert_stats.get("total_alerts", 0)}

━━━━━━━━━━━━━━━━━━━━━━
Last Cycle:
{scheduler.get("last_cycle") or "Never"}

Cycles Completed:
{scheduler.get("cycles_completed", 0)}
━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def oracle_dashboard_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 Opportunity Feed", "callback_data": "oracle_feed"}],
            [{"text": "🔍 Run Research Now", "callback_data": "oracle_run"}],
            [{"text": "🌎 Market Discovery", "callback_data": "oracle_discovery"}],
            [{"text": "🚨 Signal Changes", "callback_data": "oracle_signal_changes"}],
            [{"text": "📈 Metrics", "callback_data": "oracle_metrics"}],
            [{"text": "❤️ Health", "callback_data": "oracle_health"}],
            [{"text": "🔄 Refresh Dashboard", "callback_data": "oracle_dashboard"}],
            [{"text": "⬅ Back To Oracle", "callback_data": "oracle_menu"}],
            [{"text": "🏠 Main Menu", "callback_data": "main_menu"}],
        ]
    }


def oracle_premium_home_text():
    return """
━━━━━━━━━━━━━━━━━━━━━━
🔮 ORACLE AI
Autonomous Research Engine
━━━━━━━━━━━━━━━━━━━━━━

📊 Opportunity Feed
Live best edges

🔍 Run Research
Scan Kalshi now

🌎 Market Discovery
Find new opportunities

📈 Dashboard
System overview

👀 Watchlist
Markets being tracked

🚨 Signal Changes
Recent upgrades

❤️ Oracle Health
Service status

━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def oracle_premium_home_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📈 Oracle Dashboard", "callback_data": "oracle_dashboard"}],
            [{"text": "📊 Opportunity Feed", "callback_data": "oracle_feed"}],
            [{"text": "🔍 Run Research", "callback_data": "oracle_run"}],
            [{"text": "🌎 Market Discovery", "callback_data": "oracle_discovery"}],
            [{"text": "👀 Watchlist", "callback_data": "oracle_watchlist"}],
            [{"text": "🚨 Signal Changes", "callback_data": "oracle_signal_changes"}],
            [{"text": "❤️ Health", "callback_data": "oracle_health"}],
            [{"text": "🏠 Main Menu", "callback_data": "main_menu"}],
        ]
    }