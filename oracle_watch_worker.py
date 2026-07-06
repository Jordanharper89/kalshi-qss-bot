"""
Oracle Watch Worker

KQ-018.2B

Purpose:
- Load watched markets.
- Prioritize them using Oracle Priority Queue.
- Run fresh Oracle research.
- Compare latest signal vs previous signal.
- Save latest state.
- Pass structured change events to Notification Service.

Oracle does NOT execute trades.
Q Series handles execution.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from oracle_priority_queue import build_oracle_priority_queue
from oracle_signal_change_detector import detect_oracle_signal_changes


class OracleWatchWorker:
    def __init__(
        self,
        watchlist_service: Any,
        research_service: Any,
        notification_service: Optional[Any] = None,
        max_markets_per_cycle: int = 25,
    ):
        self.watchlist_service = watchlist_service
        self.research_service = research_service
        self.notification_service = notification_service
        self.max_markets_per_cycle = max_markets_per_cycle

    def run_once(self) -> Dict[str, Any]:
        watched_markets = self._load_watched_markets()

        if not watched_markets:
            return {
                "status": "NO_MARKETS",
                "checked": 0,
                "change_events": 0,
                "message": "No watched markets found.",
                "ran_at": self._utc_now(),
            }

        priority_queue = build_oracle_priority_queue(watched_markets)
        jobs = priority_queue[: self.max_markets_per_cycle]

        checked = 0
        total_change_events = 0
        results = []

        for job in jobs:
            ticker = job.get("ticker")

            if not ticker:
                continue

            previous_signal = self._get_previous_signal(ticker)

            latest_signal = self._run_research(ticker)

            if not latest_signal:
                results.append(
                    {
                        "ticker": ticker,
                        "status": "RESEARCH_FAILED",
                        "priority_score": job.get("priority_score"),
                    }
                )
                continue

            change_events = detect_oracle_signal_changes(
                previous_signal=previous_signal,
                latest_signal=latest_signal,
            )

            self._save_latest_signal(ticker, latest_signal, change_events)

            if change_events:
                self._send_change_events(ticker, change_events)

            checked += 1
            total_change_events += len(change_events)

            results.append(
                {
                    "ticker": ticker,
                    "status": "CHECKED",
                    "priority_score": job.get("priority_score"),
                    "change_events": len(change_events),
                    "action": latest_signal.get("action") or latest_signal.get("decision"),
                    "grade": latest_signal.get("grade"),
                    "confidence_score": latest_signal.get("confidence_score"),
                    "edge": latest_signal.get("edge"),
                }
            )

        return {
            "status": "OK",
            "checked": checked,
            "queued": len(priority_queue),
            "change_events": total_change_events,
            "results": results,
            "ran_at": self._utc_now(),
        }

    def _load_watched_markets(self) -> List[Dict[str, Any]]:
        if hasattr(self.watchlist_service, "list_watched_markets"):
            return self.watchlist_service.list_watched_markets()

        if hasattr(self.watchlist_service, "get_all"):
            return self.watchlist_service.get_all()

        if hasattr(self.watchlist_service, "list_all"):
            return self.watchlist_service.list_all()

        raise AttributeError(
            "Watchlist service must provide list_watched_markets(), get_all(), or list_all()."
        )

    def _get_previous_signal(self, ticker: str) -> Optional[Dict[str, Any]]:
        if hasattr(self.watchlist_service, "get_latest_signal"):
            return self.watchlist_service.get_latest_signal(ticker)

        if hasattr(self.watchlist_service, "get_signal_state"):
            return self.watchlist_service.get_signal_state(ticker)

        if hasattr(self.watchlist_service, "get_market"):
            market = self.watchlist_service.get_market(ticker)
            if isinstance(market, dict):
                return market.get("latest_signal") or market.get("signal")

        return None

    def _run_research(self, ticker: str) -> Optional[Dict[str, Any]]:
        if hasattr(self.research_service, "run_research"):
            return self.research_service.run_research(ticker)

        if hasattr(self.research_service, "research_market"):
            return self.research_service.research_market(ticker)

        if hasattr(self.research_service, "analyze"):
            return self.research_service.analyze(ticker)

        raise AttributeError(
            "Research service must provide run_research(), research_market(), or analyze()."
        )

    def _save_latest_signal(
        self,
        ticker: str,
        latest_signal: Dict[str, Any],
        change_events: List[Dict[str, Any]],
    ) -> None:
        payload = dict(latest_signal)
        payload["last_checked_at"] = self._utc_now()

        if change_events:
            payload["last_change_events"] = change_events
            payload["last_change_severity"] = self._highest_severity(change_events)

        if hasattr(self.watchlist_service, "save_latest_signal"):
            self.watchlist_service.save_latest_signal(ticker, payload)
            return

        if hasattr(self.watchlist_service, "update_signal_state"):
            self.watchlist_service.update_signal_state(ticker, payload)
            return

        if hasattr(self.watchlist_service, "update_market"):
            self.watchlist_service.update_market(ticker, {"latest_signal": payload})
            return

    def _send_change_events(
        self,
        ticker: str,
        change_events: List[Dict[str, Any]],
    ) -> None:
        if not self.notification_service:
            return

        if hasattr(self.notification_service, "handle_signal_changes"):
            self.notification_service.handle_signal_changes(ticker, change_events)
            return

        if hasattr(self.notification_service, "send_signal_change_events"):
            self.notification_service.send_signal_change_events(ticker, change_events)
            return

        if hasattr(self.notification_service, "notify_signal_changes"):
            self.notification_service.notify_signal_changes(ticker, change_events)
            return

    def _highest_severity(self, events: List[Dict[str, Any]]) -> str:
        severity_rank = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }

        highest = "LOW"

        for event in events:
            severity = str(event.get("severity", "LOW")).upper()
            if severity_rank.get(severity, 0) > severity_rank.get(highest, 0):
                highest = severity

        return highest

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


def run_oracle_watch_cycle(
    watchlist_service: Any,
    research_service: Any,
    notification_service: Optional[Any] = None,
    max_markets_per_cycle: int = 25,
) -> Dict[str, Any]:
    worker = OracleWatchWorker(
        watchlist_service=watchlist_service,
        research_service=research_service,
        notification_service=notification_service,
        max_markets_per_cycle=max_markets_per_cycle,
    )

    return worker.run_once()