from dataclasses import dataclass
from math import ceil
from types import MappingProxyType
from .oad_011_websocket_foundation import build_subscribe_command

OAD_012_BUILD_ID="OAD-012"
OAD_012_REVISION="OAD_012_KALSHI_SUBSCRIPTION_PARTITIONING_FULL_UNIVERSE_COVERAGE_V1"

@dataclass(frozen=True)
class SubscriptionPartition:
    partition_id:int
    market_tickers:tuple[str,...]
    channels:tuple[str,...]

@dataclass(frozen=True)
class SubscriptionCoveragePlan:
    partitions:tuple[SubscriptionPartition,...]
    eligible_markets:int
    covered_markets:int
    complete:bool

def partition_subscriptions(market_tickers,channels=("orderbook_delta","ticker","trade"),partition_size=100):
    tickers=tuple(sorted(set(str(x) for x in market_tickers if str(x))))
    if not tickers or int(partition_size)<1:
        raise ValueError("markets and positive partition_size required")
    parts=[]
    for i in range(0,len(tickers),int(partition_size)):
        chunk=tickers[i:i+int(partition_size)]
        build_subscribe_command(len(parts)+1,channels,chunk)
        parts.append(SubscriptionPartition(len(parts)+1,chunk,tuple(channels)))
    return SubscriptionCoveragePlan(tuple(parts),len(tickers),sum(len(p.market_tickers) for p in parts),True)

def build_partition_subscribe_commands(plan):
    if not isinstance(plan,SubscriptionCoveragePlan) or not plan.complete:
        raise ValueError("complete coverage plan required")
    return tuple(build_subscribe_command(p.partition_id,p.channels,p.market_tickers) for p in plan.partitions)

def build_oad_012_certification_manifest():
    return MappingProxyType({"build_id":OAD_012_BUILD_ID,"revision":OAD_012_REVISION,
        "full_universe_coverage":True,"partitioning":True,"read_only":True})

def verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage():
    p=partition_subscriptions(("C","A","B"),partition_size=2)
    return p.complete and p.covered_markets==3 and len(p.partitions)==2 and p.partitions[0].market_tickers==("A","B")
