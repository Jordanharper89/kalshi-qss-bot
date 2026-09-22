
from dataclasses import dataclass, asdict
from pathlib import Path
import json, time

from qseries_v2.oracle_source_network.persistence.live_sports_postgresql_bridge import (
    acquire_and_persist_one_per_league, ADMITTED
)

STATE_REL="qseries_v2/oracle_source_network/state/osn082_six_league_postgresql_physical_gate.json"

@dataclass(frozen=True)
class PersistenceGate:
    admitted:tuple
    committed_or_present:int
    exact_readback_verified:int
    single_writer:str
    gate_ready:bool
    execution_authority:bool=False

def run_gate(root=None):
    base=Path(root or Path.cwd()).resolve()
    rows,_=acquire_and_persist_one_per_league(root=base,timeout=15,commit_timeout_seconds=45.0)
    exact=sum(1 for r in rows if r.readback_count>0)
    if exact != len(ADMITTED):
        raise RuntimeError(f"exact readback mismatch: expected={len(ADMITTED)} actual={exact}")
    result=PersistenceGate(
        admitted=ADMITTED,
        committed_or_present=len(rows),
        exact_readback_verified=exact,
        single_writer="OPH-019",
        gate_ready=True,
    )
    state=base/STATE_REL
    state.write_text(json.dumps({
        **asdict(result),
        "admitted":list(result.admitted),
    },indent=2),encoding="utf-8")
    return result,state
