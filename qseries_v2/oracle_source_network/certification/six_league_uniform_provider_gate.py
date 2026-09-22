
from dataclasses import dataclass, asdict
from pathlib import Path
import json, time

from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events

ADMITTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")
STATE_REL="qseries_v2/oracle_source_network/state/osn078_six_league_uniform_physical_gate.json"

@dataclass(frozen=True)
class PhysicalRow:
    league:str
    events:int
    unique_provider_ids:int
    elapsed_seconds:float
    authority:str
    callable_name:str
    execution_authority:bool=False

def run_gate(root=None, timeout=15):
    base=Path(root or Path.cwd()).resolve()
    rows=[]
    for league in ADMITTED:
        started=time.monotonic()
        r=acquire_canonical_events(league,timeout=timeout,root=base)
        elapsed=round(time.monotonic()-started,3)
        if r.event_count < 1:
            raise RuntimeError(f"{league} returned zero canonical events")

        provider_ids=[]
        for event in r.events:
            pid=str(getattr(event,"provider_event_id","") or "")
            if pid:
                provider_ids.append(pid)

        unique_ids=len(set(provider_ids))
        if unique_ids < 1:
            raise RuntimeError(f"{league} returned no provider event identities")

        row=PhysicalRow(
            league=league,
            events=r.event_count,
            unique_provider_ids=unique_ids,
            elapsed_seconds=elapsed,
            authority=r.authority,
            callable_name=r.callable_name,
        )
        rows.append(row)
        print(
            f"[PHYSICAL] {league} events={row.events} "
            f"unique_provider_ids={row.unique_provider_ids} "
            f"elapsed={row.elapsed_seconds}s "
            f"authority={row.authority} callable={row.callable_name}"
        )

    state=base/STATE_REL
    state.parent.mkdir(parents=True,exist_ok=True)
    state.write_text(json.dumps({
        "rows":[asdict(x) for x in rows],
        "admitted":list(ADMITTED),
        "held":["NCAAB","MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED"],
        "blocked":["UCL"],
        "uniform_provider":"qseries_v2.oracle_source_network.providers.uniform_sports_provider:acquire_canonical_events",
        "execution_authority":False,
    },indent=2),encoding="utf-8")
    return tuple(rows),state
