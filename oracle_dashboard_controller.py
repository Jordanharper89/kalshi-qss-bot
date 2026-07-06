"""
Oracle Dashboard Controller

ORACLE-024.2

Purpose:
- Connect Oracle Dashboard Engine to Oracle Dashboard UI.
- Returns text + keyboard.
- No Telegram sending.
"""

from oracle_dashboard_ui import (
    oracle_dashboard_text,
    oracle_dashboard_keyboard,
    oracle_premium_home_text,
    oracle_premium_home_keyboard,
)


class OracleDashboardController:

    def __init__(self, dashboard_engine=None):
        self.dashboard_engine = dashboard_engine

    def home(self):

        return (
            oracle_premium_home_text(),
            oracle_premium_home_keyboard(),
        )

    def dashboard(self):

        snapshot = {}

        if self.dashboard_engine:
            snapshot = self.dashboard_engine.snapshot()

        return (
            oracle_dashboard_text(snapshot),
            oracle_dashboard_keyboard(),
        )

    def placeholder(self, title):

        text = f"""
━━━━━━━━━━━━━━━━━━━━━━
🔮 {title}
━━━━━━━━━━━━━━━━━━━━━━

Status:
This screen is ready for the next build.

━━━━━━━━━━━━━━━━━━━━━━
""".strip()

        keyboard = {
            "inline_keyboard": [
                [{"text": "⬅ Back To Oracle", "callback_data": "oracle_menu"}],
                [{"text": "🏠 Main Menu", "callback_data": "main_menu"}],
            ]
        }

        return text, keyboard