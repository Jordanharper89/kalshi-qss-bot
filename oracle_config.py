"""
Oracle Configuration

ORACLE-021.8

Purpose:
- Central configuration for Oracle.
- Eliminates hardcoded values.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class OracleConfig:
    # Discovery
    discovery_interval_seconds: int = 180
    min_volume: float = 100.0
    min_liquidity: float = 100.0
    max_discovery_candidates: int = 25
    auto_add_limit: int = 10

    # Research
    max_research_markets_per_cycle: int = 25

    # Opportunity Feed
    opportunity_feed_size: int = 10
    min_grade: str = "B+"
    min_edge: float = 2.0
    min_confidence: float = 60.0

    # Watchlist
    max_watchlist_size: int = 500

    # Scheduler
    scheduler_enabled: bool = True

    # Notifications
    notify_grade_upgrades: bool = True
    notify_action_changes: bool = True
    notify_edge_changes: bool = True
    notify_confidence_changes: bool = True

    # Categories
    preferred_categories: List[str] = field(
        default_factory=lambda: [
            "crypto",
            "economy",
            "politics",
            "sports",
            "weather",
        ]
    )

    # Logging
    enable_debug_logging: bool = False
    enable_performance_logging: bool = True


oracle_config = OracleConfig()