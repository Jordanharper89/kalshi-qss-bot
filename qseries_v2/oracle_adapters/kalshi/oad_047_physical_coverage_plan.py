from __future__ import annotations
from dataclasses import dataclass
from .oad_041_full_universe_partitioning import build_full_universe_partition_plan
OAD_047_BUILD_ID="OAD-047"
OAD_047_REVISION="OAD_047_GLOBAL_FAST_LANE_AND_ORDERBOOK_PARTITION_PLAN_V1"
@dataclass(frozen=True)
class PhysicalCoveragePlan:
    global_channels:tuple[str,...]; global_market_filter:None; orderbook_partitions:tuple; total_open_markets:int; complete:bool
def build_physical_coverage_plan(open_market_tickers,orderbook_partition_size=100):
    p=build_full_universe_partition_plan(open_market_tickers,orderbook_partition_size)
    return PhysicalCoveragePlan(("ticker","trade"),None,p.partitions,p.total_markets,p.complete)
def verify_oad_047_global_fast_lane_and_orderbook_partition_plan():
    p=build_physical_coverage_plan(("A","B","C"),2)
    return p.global_market_filter is None and len(p.orderbook_partitions)==2 and p.complete
