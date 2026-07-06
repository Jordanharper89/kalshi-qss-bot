"""
OI-058 Oracle Opportunity Queue Manager

Purpose:
- Maintain a stable read-only priority queue of Oracle opportunities.
- Accept output from OI-057 Opportunity Discovery Engine.
- Deduplicate tickers, preserve highest score, and expose next items for research.
- Prevent repeated noisy processing of the same low-change market.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class OracleOpportunityQueueManager:
    module_name = "oi_058_oracle_opportunity_queue_manager"

    def __init__(self) -> None:
        self._queue: Dict[str, Dict[str, Any]] = {}
        self._processed: Dict[str, Dict[str, Any]] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "queued": len(self._queue),
            "processed": len(self._processed),
        }

    def clear(self) -> Dict[str, Any]:
        self._queue.clear()
        self._processed.clear()
        return {
            "status": "ok",
            "read_only": True,
            "queued": 0,
            "processed": 0,
        }

    def ingest_discovery_result(self, discovery_result: Dict[str, Any]) -> Dict[str, Any]:
        opportunities = discovery_result.get("top_opportunities", []) or []
        added = 0
        updated = 0
        skipped = 0

        for opportunity in opportunities:
            result = self.enqueue(opportunity)
            if result["action"] == "added":
                added += 1
            elif result["action"] == "updated":
                updated += 1
            else:
                skipped += 1

        return {
            "status": "ok",
            "read_only": True,
            "added": added,
            "updated": updated,
            "skipped": skipped,
            "queued": len(self._queue),
        }

    def enqueue(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        ticker = self._ticker(opportunity)

        if not ticker:
            return {
                "status": "skipped",
                "read_only": True,
                "action": "skipped",
                "reason": "missing_ticker",
            }

        now = self._now()
        existing = self._queue.get(ticker)

        incoming = dict(opportunity)
        incoming["ticker"] = ticker
        incoming["queued_at"] = existing.get("queued_at") if existing else now
        incoming["updated_at"] = now
        incoming["queue_status"] = "queued"

        if existing:
            old_score = float(existing.get("opportunity_score", 0.0))
            new_score = float(incoming.get("opportunity_score", 0.0))

            if new_score >= old_score:
                incoming["queue_updates"] = int(existing.get("queue_updates", 0)) + 1
                self._queue[ticker] = incoming
                return {
                    "status": "ok",
                    "read_only": True,
                    "action": "updated",
                    "ticker": ticker,
                }

            return {
                "status": "ok",
                "read_only": True,
                "action": "skipped",
                "ticker": ticker,
                "reason": "existing_score_higher",
            }

        incoming["queue_updates"] = 0
        self._queue[ticker] = incoming

        return {
            "status": "ok",
            "read_only": True,
            "action": "added",
            "ticker": ticker,
        }

    def next_opportunity(
        self,
        min_score: float = 0.0,
        allowed_priorities: Optional[List[str]] = None,
        mark_reserved: bool = True,
    ) -> Optional[Dict[str, Any]]:
        items = self.peek(
            limit=1,
            min_score=min_score,
            allowed_priorities=allowed_priorities,
        )

        if not items:
            return None

        item = items[0]

        if mark_reserved:
            ticker = item["ticker"]
            if ticker in self._queue:
                self._queue[ticker]["queue_status"] = "reserved"
                self._queue[ticker]["reserved_at"] = self._now()

        return item

    def peek(
        self,
        limit: int = 10,
        min_score: float = 0.0,
        allowed_priorities: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        allowed = set(allowed_priorities or [])

        items = []

        for item in self._queue.values():
            if float(item.get("opportunity_score", 0.0)) < min_score:
                continue

            if allowed and item.get("priority") not in allowed:
                continue

            items.append(dict(item))

        items.sort(
            key=lambda x: (
                float(x.get("opportunity_score", 0.0)),
                int(x.get("priority_weight", 0)),
                str(x.get("updated_at", "")),
            ),
            reverse=True,
        )

        for idx, item in enumerate(items, start=1):
            item["queue_rank"] = idx

        return items[:limit]

    def mark_processed(
        self,
        ticker: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if ticker not in self._queue:
            return {
                "status": "not_found",
                "read_only": True,
                "ticker": ticker,
            }

        item = self._queue.pop(ticker)
        item["queue_status"] = "processed"
        item["processed_at"] = self._now()
        item["process_result"] = result or {}

        self._processed[ticker] = item

        return {
            "status": "ok",
            "read_only": True,
            "ticker": ticker,
            "queued": len(self._queue),
            "processed": len(self._processed),
        }

    def mark_skipped(
        self,
        ticker: str,
        reason: str = "skipped",
    ) -> Dict[str, Any]:
        return self.mark_processed(
            ticker=ticker,
            result={
                "status": "skipped",
                "reason": reason,
            },
        )

    def requeue(
        self,
        ticker: str,
    ) -> Dict[str, Any]:
        if ticker not in self._processed:
            return {
                "status": "not_found",
                "read_only": True,
                "ticker": ticker,
            }

        item = self._processed.pop(ticker)
        item["queue_status"] = "queued"
        item["requeued_at"] = self._now()
        self._queue[ticker] = item

        return {
            "status": "ok",
            "read_only": True,
            "ticker": ticker,
            "queued": len(self._queue),
            "processed": len(self._processed),
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "read_only": True,
            "queued": self.peek(limit=100000),
            "processed": list(self._processed.values()),
            "counts": {
                "queued": len(self._queue),
                "processed": len(self._processed),
            },
        }

    def _ticker(self, opportunity: Dict[str, Any]) -> Optional[str]:
        value = (
            opportunity.get("ticker")
            or opportunity.get("market_ticker")
            or opportunity.get("id")
            or opportunity.get("market", {}).get("ticker")
            or opportunity.get("market", {}).get("market_ticker")
        )

        return str(value) if value else None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_opportunity_queue_manager = OracleOpportunityQueueManager()
