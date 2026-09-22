from dataclasses import dataclass
OAD_041_BUILD_ID="OAD-041"
OAD_041_REVISION="OAD_041_FULL_UNIVERSE_STREAM_PARTITION_EXPANSION_V1"

@dataclass(frozen=True)
class FullUniverseStreamPartition:
    partition_id:int
    market_tickers:tuple[str,...]

@dataclass(frozen=True)
class FullUniversePartitionPlan:
    partitions:tuple[FullUniverseStreamPartition,...]
    total_markets:int
    partition_size:int
    complete:bool

def build_full_universe_partition_plan(market_tickers,partition_size=100):
    size=int(partition_size)
    if size<1:
        raise ValueError("partition_size must be positive")
    tickers=tuple(sorted(set(str(x).strip() for x in market_tickers if str(x).strip())))
    if not tickers:
        raise ValueError("market_tickers required")
    parts=[]
    for i in range(0,len(tickers),size):
        parts.append(FullUniverseStreamPartition(len(parts)+1,tickers[i:i+size]))
    parts=tuple(parts)
    flat=tuple(t for p in parts for t in p.market_tickers)
    return FullUniversePartitionPlan(parts,len(tickers),size,flat==tickers)

def verify_oad_041_full_universe_stream_partition_expansion():
    p=build_full_universe_partition_plan(("C","A","B","D"),2)
    return p.complete and p.total_markets==4 and len(p.partitions)==2 and p.partitions[0].market_tickers==("A","B")
