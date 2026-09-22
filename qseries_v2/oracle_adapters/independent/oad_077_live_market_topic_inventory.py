from __future__ import annotations
from collections import Counter
from dataclasses import dataclass

from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index
from qseries_v2.oracle_adapters.independent.oad_076_precision_current_market_topic_classifier import classify_market_cohort

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class LiveTopicInventory:
    market_count:int
    classified_count:int
    unclassified_count:int
    topic_counts:tuple[tuple[str,int],...]
    classifications:tuple

def build_live_topic_inventory(limit=1000):
    markets,_=fetch_current_open_kalshi_market_index(limit=limit)
    classes=classify_market_cohort(markets)
    counts=Counter(x.primary_topic for x in classes)
    unclassified=counts.get("other",0)
    return LiveTopicInventory(
        len(markets),
        len(markets)-unclassified,
        unclassified,
        tuple(sorted(counts.items(),key=lambda kv:(-kv[1],kv[0]))),
        classes,
    )
