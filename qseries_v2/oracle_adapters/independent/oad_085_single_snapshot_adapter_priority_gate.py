from __future__ import annotations
from dataclasses import dataclass

from qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort
from qseries_v2.oracle_adapters.independent.oad_084_hierarchical_source_demand_map import source_demand_from_snapshot

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class AdapterPriority:
    rank:int
    topic:str
    source_family:str
    live_markets:int
    state:str

@dataclass(frozen=True,slots=True)
class PhysicalAdapterPriorityGate:
    snapshot_id:str
    evaluated_markets:int
    priorities:tuple[AdapterPriority,...]
    unresolved_markets:int

def build_physical_adapter_priority_gate(limit=1000,max_priorities=12):
    snapshot=capture_current_market_cohort(limit)
    demand=source_demand_from_snapshot(snapshot)
    candidates=[]
    unresolved=0
    for d in demand:
        if d.state=="UNMAPPED":
            unresolved+=d.live_markets
            continue
        for fam in d.missing_families:
            candidates.append((d.live_markets,d.topic,fam,d.state))
    candidates.sort(key=lambda x:(-x[0],x[1],x[2]))
    priorities=tuple(
        AdapterPriority(i+1,topic,fam,count,state)
        for i,(count,topic,fam,state) in enumerate(candidates[:int(max_priorities)])
    )
    return PhysicalAdapterPriorityGate(snapshot.snapshot_id,snapshot.market_count,priorities,unresolved)
