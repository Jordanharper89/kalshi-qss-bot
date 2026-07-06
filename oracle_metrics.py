"""
Oracle Metrics

ORACLE-021.6

Purpose:
- Collect Oracle runtime statistics.
- Track research performance.
- Track discovery performance.
- Track signal performance.
"""

from datetime import datetime, timezone


class OracleMetrics:

    def __init__(self):

        self.reset()

    def reset(self):

        self.started_at = self._utc_now()

        self.total_cycles = 0
        self.total_markets_scanned = 0
        self.total_markets_discovered = 0
        self.total_markets_added = 0
        self.total_markets_researched = 0
        self.total_signal_changes = 0

    def update(self, pipeline_result):

        summary = pipeline_result.get("summary", {})

        self.total_cycles += 1

        self.total_markets_scanned += summary.get(
            "raw_markets_scanned",
            0,
        )

        self.total_markets_discovered += summary.get(
            "markets_discovered",
            0,
        )

        self.total_markets_added += summary.get(
            "markets_added_to_watchlist",
            0,
        )

        self.total_markets_researched += summary.get(
            "markets_researched",
            0,
        )

        self.total_signal_changes += summary.get(
            "signal_change_events",
            0,
        )

    def snapshot(self):

        return {
            "started_at": self.started_at,

            "total_cycles": self.total_cycles,

            "markets_scanned": self.total_markets_scanned,

            "markets_discovered": self.total_markets_discovered,

            "markets_added": self.total_markets_added,

            "markets_researched": self.total_markets_researched,

            "signal_changes": self.total_signal_changes,
        }

    def _utc_now(self):

        return datetime.now(
            timezone.utc
        ).isoformat()