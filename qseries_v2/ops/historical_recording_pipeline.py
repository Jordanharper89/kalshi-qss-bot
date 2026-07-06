"""
OPS-004 — Historical Recording Pipeline

Purpose:
- Connect ADP-013 Live Market Cache to OPS-003 Historical Data Store.
- Automatically record cached market snapshots.
- Skip duplicates when nothing meaningful changed.
- Track write performance, skipped snapshots, and errors.

No trading logic.
No execution logic.
"""

import time
import hashlib
import json
from typing import Any, Dict, Optional


class HistoricalRecordingPipelineError(Exception):
    pass


class HistoricalRecordingPipeline:
    def __init__(
        self,
        market_cache: Any,
        historical_store: Any,
        event_bus: Any = None,
        skip_duplicates: bool = True,
        source: str = "adp.market_cache",
    ):
        if market_cache is None:
            raise HistoricalRecordingPipelineError("market_cache is required.")

        if historical_store is None:
            raise HistoricalRecordingPipelineError("historical_store is required.")

        self.market_cache = market_cache
        self.historical_store = historical_store
        self.event_bus = event_bus
        self.skip_duplicates = bool(skip_duplicates)
        self.source = source

        self.started_at = time.time()
        self.record_count = 0
        self.market_rows_recorded = 0
        self.skipped_duplicates = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.last_recorded_at: Optional[float] = None
        self.last_duration_seconds: Optional[float] = None
        self.last_snapshot_hash: Optional[str] = None
        self.last_result: Optional[Dict[str, Any]] = None

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        if self.event_bus is None:
            return

        try:
            if hasattr(self.event_bus, "publish"):
                self.event_bus.publish(event_type, payload)
            elif hasattr(self.event_bus, "emit"):
                self.event_bus.emit(event_type, payload)
        except Exception:
            pass

    def _snapshot_hash(self, markets):
        lightweight = []

        for market in markets:
            lightweight.append({
                "ticker": market.get("ticker"),
                "yes_bid": market.get("yes_bid"),
                "yes_ask": market.get("yes_ask"),
                "no_bid": market.get("no_bid"),
                "no_ask": market.get("no_ask"),
                "last_price": market.get("last_price"),
                "volume": market.get("volume"),
                "open_interest": market.get("open_interest"),
                "liquidity": market.get("liquidity"),
                "status": market.get("status"),
            })

        lightweight.sort(key=lambda x: x.get("ticker") or "")
        raw = json.dumps(lightweight, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def record_current_snapshot(self, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        started = time.time()

        try:
            markets = self.market_cache.get_all_markets()
            snapshot_hash = self._snapshot_hash(markets)

            if self.skip_duplicates and self.last_snapshot_hash == snapshot_hash:
                self.skipped_duplicates += 1
                result = {
                    "module": "ops_004_historical_recording_pipeline",
                    "status": "skipped_duplicate",
                    "market_count": len(markets),
                    "inserted_count": 0,
                    "skipped_duplicates": self.skipped_duplicates,
                    "duration_seconds": round(time.time() - started, 4),
                    "timestamp": time.time(),
                }
                self.last_result = result
                self._emit("ops.history.pipeline.skipped", result)
                return result

            result = self.historical_store.record_snapshot(
                markets=markets,
                source=self.source,
                metadata={
                    "pipeline": "OPS-004",
                    "snapshot_hash": snapshot_hash,
                    **(metadata or {}),
                },
            )

            self.last_snapshot_hash = snapshot_hash
            self.record_count += 1
            self.market_rows_recorded += int(result.get("inserted_count") or 0)
            self.last_recorded_at = time.time()
            self.last_duration_seconds = time.time() - started
            self.last_error = None

            pipeline_result = {
                "module": "ops_004_historical_recording_pipeline",
                "status": result.get("status"),
                "market_count": result.get("market_count"),
                "inserted_count": result.get("inserted_count"),
                "record_count": self.record_count,
                "market_rows_recorded": self.market_rows_recorded,
                "duration_seconds": round(self.last_duration_seconds, 4),
                "store_result": result,
                "timestamp": self.last_recorded_at,
            }

            self.last_result = pipeline_result
            self._emit("ops.history.pipeline.recorded", pipeline_result)
            return pipeline_result

        except Exception as exc:
            self.error_count += 1
            self.last_error = str(exc)
            self.last_duration_seconds = time.time() - started

            result = {
                "module": "ops_004_historical_recording_pipeline",
                "status": "error",
                "error": str(exc),
                "error_count": self.error_count,
                "duration_seconds": round(self.last_duration_seconds, 4),
                "timestamp": time.time(),
            }

            self.last_result = result
            self._emit("ops.history.pipeline.error", result)
            return result

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "ops_004_historical_recording_pipeline",
            "status": "ok" if self.error_count == 0 else "warning",
            "source": self.source,
            "skip_duplicates": self.skip_duplicates,
            "record_count": self.record_count,
            "market_rows_recorded": self.market_rows_recorded,
            "skipped_duplicates": self.skipped_duplicates,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_recorded_at": self.last_recorded_at,
            "last_duration_seconds": self.last_duration_seconds,
            "has_snapshot_hash": self.last_snapshot_hash is not None,
            "last_result": self.last_result,
            "read_only_trading": True,
        }


def build_historical_recording_pipeline(
    market_cache: Any,
    historical_store: Any,
    event_bus: Any = None,
    skip_duplicates: bool = True,
    source: str = "adp.market_cache",
) -> HistoricalRecordingPipeline:
    return HistoricalRecordingPipeline(
        market_cache=market_cache,
        historical_store=historical_store,
        event_bus=event_bus,
        skip_duplicates=skip_duplicates,
        source=source,
    )


if __name__ == "__main__":
    print("OPS-004 Historical Recording Pipeline installed.")
