"""
Oracle Continuous Research Pipeline

KQ-018.4

Purpose:
- Run Oracle Discovery Worker.
- Add discovered markets to Oracle Watchlist.
- Run Oracle Watch Worker.
- Research watched markets by priority.
- Detect signal changes.
- Return one clean cycle summary.

Oracle does NOT execute trades.
Q Series handles execution.
Telegram is UI only.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from oracle_discovery_worker import run_oracle_discovery_cycle
from oracle_watch_worker import run_oracle_watch_cycle


class OracleContinuousResearchPipeline:
    def __init__(
        self,
        market_data_service: Any,
        watchlist_service: Any,
        research_service: Any,
        notification_service: Optional[Any] = None,
        preferred_categories: Optional[List[str]] = None,
        min_volume: float = 100.0,
        min_liquidity: float = 100.0,
        max_discovery_candidates: int = 25,
        auto_add_limit: int = 10,
        max_research_markets_per_cycle: int = 25,
    ):
        self.market_data_service = market_data_service
        self.watchlist_service = watchlist_service
        self.research_service = research_service
        self.notification_service = notification_service

        self.preferred_categories = preferred_categories or []
        self.min_volume = min_volume
        self.min_liquidity = min_liquidity
        self.max_discovery_candidates = max_discovery_candidates
        self.auto_add_limit = auto_add_limit
        self.max_research_markets_per_cycle = max_research_markets_per_cycle

    def run_once(self) -> Dict[str, Any]:
        started_at = self._utc_now()

        discovery_result = self._run_discovery()
        research_result = self._run_research()

        return {
            "status": "OK",
            "pipeline": "ORACLE_CONTINUOUS_RESEARCH",
            "started_at": started_at,
            "finished_at": self._utc_now(),
            "discovery": discovery_result,
            "research": research_result,
            "summary": self._build_summary(discovery_result, research_result),
        }

    def _run_discovery(self) -> Dict[str, Any]:
        try:
            return run_oracle_discovery_cycle(
                market_data_service=self.market_data_service,
                watchlist_service=self.watchlist_service,
                preferred_categories=self.preferred_categories,
                min_volume=self.min_volume,
                min_liquidity=self.min_liquidity,
                max_candidates=self.max_discovery_candidates,
                auto_add_limit=self.auto_add_limit,
            )

        except Exception as error:
            return {
                "status": "ERROR",
                "stage": "DISCOVERY",
                "error": str(error),
                "ran_at": self._utc_now(),
            }

    def _run_research(self) -> Dict[str, Any]:
        try:
            return run_oracle_watch_cycle(
                watchlist_service=self.watchlist_service,
                research_service=self.research_service,
                notification_service=self.notification_service,
                max_markets_per_cycle=self.max_research_markets_per_cycle,
            )

        except Exception as error:
            return {
                "status": "ERROR",
                "stage": "RESEARCH",
                "error": str(error),
                "ran_at": self._utc_now(),
            }

    def _build_summary(
        self,
        discovery_result: Dict[str, Any],
        research_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "raw_markets_scanned": discovery_result.get("raw_markets", 0),
            "markets_discovered": discovery_result.get("discovered", 0),
            "markets_added_to_watchlist": discovery_result.get("added", 0),
            "markets_researched": research_result.get("checked", 0),
            "queued_markets": research_result.get("queued", 0),
            "signal_change_events": research_result.get("change_events", 0),
            "discovery_status": discovery_result.get("status"),
            "research_status": research_result.get("status"),
        }

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def run_oracle_continuous_research_pipeline(
    market_data_service: Any,
    watchlist_service: Any,
    research_service: Any,
    notification_service: Optional[Any] = None,
    preferred_categories: Optional[List[str]] = None,
    min_volume: float = 100.0,
    min_liquidity: float = 100.0,
    max_discovery_candidates: int = 25,
    auto_add_limit: int = 10,
    max_research_markets_per_cycle: int = 25,
) -> Dict[str, Any]:
    pipeline = OracleContinuousResearchPipeline(
        market_data_service=market_data_service,
        watchlist_service=watchlist_service,
        research_service=research_service,
        notification_service=notification_service,
        preferred_categories=preferred_categories,
        min_volume=min_volume,
        min_liquidity=min_liquidity,
        max_discovery_candidates=max_discovery_candidates,
        auto_add_limit=auto_add_limit,
        max_research_markets_per_cycle=max_research_markets_per_cycle,
    )

    return pipeline.run_once()