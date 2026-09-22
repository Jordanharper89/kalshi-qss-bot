from dataclasses import dataclass

OIS_038_BUILD_ID="OIS-038"
OIS_038_REVISION="OIS_038_FULL_UNIVERSE_RECONCILIATION_V1"

@dataclass(frozen=True)
class UniverseReconciliation:
    discovered:int
    previous:int
    added:tuple[str,...]
    removed:tuple[str,...]
    unchanged:tuple[str,...]
    complete:bool

def reconcile_market_universe(previous_ids,discovered_ids):
    prev=set(previous_ids)
    new=set(discovered_ids)
    if not new:
        raise ValueError("discovered universe cannot be empty")
    added=tuple(sorted(new-prev))
    removed=tuple(sorted(prev-new))
    unchanged=tuple(sorted(prev & new))
    complete=len(new)==len(set(discovered_ids))
    return UniverseReconciliation(len(new),len(prev),added,removed,unchanged,complete)

def verify_ois_038_full_universe_reconciliation():
    r=reconcile_market_universe(("A","B"),("B","C"))
    return r.added==("C",) and r.removed==("A",) and r.unchanged==("B",) and r.complete
