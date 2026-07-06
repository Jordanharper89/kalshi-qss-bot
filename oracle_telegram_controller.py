"""
Oracle Telegram Controller

ORACLE-021.3

Purpose:
- One controller for Oracle Telegram actions.
- Connects Oracle Session Manager to Telegram UI formatters.
- Returns text + keyboard.
- Does NOT send Telegram messages directly.
"""

from typing import Any, Dict, Tuple

from oracle_telegram_session_ui import (
    oracle_home_text,
    oracle_home_keyboard,
    format_oracle_run_result,
    format_oracle_status_text,
)

from telegram_oracle_feed_formatter import format_oracle_feed_message


class OracleTelegramController:
    def __init__(self, oracle_session_manager: Any):
        self.oracle = oracle_session_manager

    def home(self) -> Tuple[str, Dict[str, Any]]:
        return oracle_home_text(), oracle_home_keyboard()

    def opportunity_feed(self) -> Tuple[str, Dict[str, Any]]:
        opportunities = self.oracle.build_opportunity_feed(
            min_grade="B+",
            min_edge=2.0,
            min_confidence=60.0,
            max_items=10,
        )

        text = format_oracle_feed_message(opportunities)
        keyboard = self.back_keyboard()

        return text, keyboard

    def run_research_cycle(self) -> Tuple[str, Dict[str, Any]]:
        result = self.oracle.run_once()
        text = format_oracle_run_result(result)
        keyboard = self.back_keyboard()

        return text, keyboard

    def status(self) -> Tuple[str, Dict[str, Any]]:
        status = self.oracle.get_status()
        text = format_oracle_status_text(status)
        keyboard = self.back_keyboard()

        return text, keyboard

    def placeholder(self, title: str) -> Tuple[str, Dict[str, Any]]:
        text = f"""
🔮 {title}

Status:
This Oracle screen is reserved for the next build.
""".strip()

        return text, self.back_keyboard()

    def back_keyboard(self) -> Dict[str, Any]:
        return {
            "inline_keyboard": [
                [{"text": "Back To Oracle", "callback_data": "oracle_menu"}],
                [{"text": "Back To Main Menu", "callback_data": "main_menu"}],
            ]
        }