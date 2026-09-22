
from dataclasses import dataclass, asdict
from pathlib import Path
import json

from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events
from qseries_v2.oracle_source_network.persistence.live_sports_postgresql_bridge import persist_event

STATE_REL="qseries_v2/oracle_source_network/state/osn083_restart_idempotency_gate.json"

@dataclass(frozen=True)
class RestartIdempotencyResult:
    league:str
    observation_id:str
    first_action:str
    replay_action:str
    replay_resubmitted:bool
    exact_readback:int
    execution_authority:bool=False

def run_gate(root=None,league="NHL"):
    base=Path(root or Path.cwd()).resolve()
    result=acquire_canonical_events(league,timeout=15,root=base)
    if not result.events:
        raise RuntimeError(f"{league} returned zero events")
    event=result.events[0]

    first=persist_event(league,event,root=base,batch_id="osn083-first")
    replay=persist_event(league,event,root=base,batch_id="osn083-replay")

    if first.observation_id != replay.observation_id:
        raise RuntimeError("canonical observation identity changed across replay")
    replay_resubmitted=(replay.write_action!="READ_BEFORE_WRITE_HIT")
    if replay_resubmitted:
        raise RuntimeError(f"replay was resubmitted: {replay.write_action}")

    out=RestartIdempotencyResult(
        league=league,
        observation_id=first.observation_id,
        first_action=first.write_action,
        replay_action=replay.write_action,
        replay_resubmitted=False,
        exact_readback=replay.readback_count,
    )
    state=base/STATE_REL
    state.write_text(json.dumps(asdict(out),indent=2),encoding="utf-8")
    return out,state
