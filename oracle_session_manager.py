"""
Oracle Session Manager

ORACLE-021.1

Purpose:
- Master controller for Oracle.
- Runs one full Oracle research cycle.
- Tracks status.
- Prevents duplicate cycles from running at the same time.
- Does NOT execute trades.
"""

import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from oracle_continuous_research_pipeline import run_oracle_continuous_research_pipeline
from oracle_opportunity_feed import build_oracle_opportunity_feed


class OracleSessionManager:
    def __init__(
        self,
        market_data_service: Any,
        watchlist_service: Any,
        research_service: Any,
        notification_service: Optional[Any] = None,
        preferred_categories=None,
    ):
        self.market_data_service = market_data_service
        self.watchlist_service = watchlist_service
        self.research_service = research_service
        self.notification_service = notification_service
        self.preferred_categories = preferred_categories or []

        self._lock = threading.Lock()
        self.status = "IDLE"
        self.last_started_at = None
        self.last_finished_at = None
        self.last_error = None
        self.last_result = None

    def run_once(self) -> Dict[str, Any]:
        if not self._lock.acquire(blocking=False):
            return {
                "status": "BUSY",
                "message": "Oracle research cycle is already running.",
                "started_at": self.last_started_at,
            }

        try:
            self.status = "RUNNING"
            self.last_error = None
            self.last_started_at = self._utc_now()

            result = run_oracle_continuous_research_pipeline(
                market_data_service=self.market_data_service,
                watchlist_service=self.watchlist_service,
                research_service=self.research_service,
                notification_service=self.notification_service,
                preferred_categories=self.preferred_categories,
                min_volume=100.0,
                min_liquidity=100.0,
                max_discovery_candidates=25,
                auto_add_limit=10,
                max_research_markets_per_cycle=25,
            )

            self.last_result = result
            self.status = "IDLE"
            self.last_finished_at = self._utc_now()

            return result

        except Exception as error:
            self.status = "ERROR"
            self.last_error = str(error)
            self.last_finished_at = self._utc_now()

            return {
                "status": "ERROR",
                "error": str(error),
                "started_at": self.last_started_at,
                "finished_at": self.last_finished_at,
            }

        finally:
            self._lock.release()

    def build_opportunity_feed(
        self,
        min_grade: str = "B+",
        min_edge: float = 2.0,
        min_confidence: float = 60.0,
        max_items: int = 10,
    ):
        watched_markets = self._load_watched_markets()

        return build_oracle_opportunity_feed(
            watched_markets=watched_markets,
            min_grade=min_grade,
            min_edge=min_edge,
            min_confidence=min_confidence,
            max_items=max_items,
        )

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "last_started_at": self.last_started_at,
            "last_finished_at": self.last_finished_at,
            "last_error": self.last_error,
            "last_summary": self._last_summary(),
        }

    def _last_summary(self):
        if not isinstance(self.last_result, dict):
            return None

        return self.last_result.get("summary") or self.last_result

    def _load_watched_markets(self):
        if hasattr(self.watchlist_service, "list_watched_markets"):
            return self.watchlist_service.list_watched_markets() or []

        if hasattr(self.watchlist_service, "get_all"):
            return self.watchlist_service.get_all() or []

        if hasattr(self.watchlist_service, "list_all"):
            return self.watchlist_service.list_all() or []

        return []

    def _utc_now(self):
        return datetime.now(timezone.utc).isoformat()


def format_oracle_status(status: Dict[str, Any]) -> str:
    summary = status.get("last_summary") or {}

    return f"""
🔮 ORACLE STATUS

State:
{status.get("status")}

Last Started:
{status.get("last_started_at") or "Never"}

Last Finished:
{status.get("last_finished_at") or "Never"}

Last Error:
{status.get("last_error") or "None"}

Last Cycle:
Markets Scanned: {summary.get("raw_markets_scanned", 0)}
Markets Added: {summary.get("markets_added_to_watchlist", 0)}
Markets Researched: {summary.get("markets_researched", 0)}
Signal Changes: {summary.get("signal_change_events", 0)}
""".strip()