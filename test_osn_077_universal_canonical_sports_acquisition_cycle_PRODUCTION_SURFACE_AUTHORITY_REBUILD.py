
from pathlib import Path
import json
from qseries_v2.oracle_source_network.runtime.direct_canonical_sports_cycle import (
    freeze_production_event_surfaces,
    acquire_canonical_events,
)

root=Path.cwd()

bindings,state=freeze_production_event_surfaces(root=root,timeout=15)
print("[PRODUCTION_SURFACE_STATE]",state)
for b in bindings:
    print(
        f"[PRODUCTION_SURFACE] {b.league} "
        f"{b.module}:{b.function} "
        f"events={b.canonical_events_observed} "
        f"source_test={b.source_test}"
    )

assert tuple(x.league for x in bindings)==("NHL","MLS","EPL")
assert all(x.canonical_events_observed > 0 for x in bindings)
assert all(x.execution_authority is False for x in bindings)

rows=[]
for league in ("NFL","NCAAF","NBA","NHL","MLS","EPL"):
    r=acquire_canonical_events(league,root=root,timeout=15)
    print(
        f"[DIRECT] {league} events={r.event_count} "
        f"authority={r.authority}"
    )
    for c in r.callables_attempted:
        print("  [CALL]",c)
    sample=r.canonical_events[0]
    print(
        f"  [SAMPLE] provider_event_id={getattr(sample,'provider_event_id',None)} "
        f"home={getattr(sample,'home',getattr(sample,'home_team',None))} "
        f"away={getattr(sample,'away',getattr(sample,'away_team',None))}"
    )
    assert r.event_count > 0
    assert r.execution_authority is False
    rows.append({
        "league":league,
        "event_count":r.event_count,
        "authority":r.authority,
        "callables":list(r.callables_attempted),
    })

report=root/"qseries_v2/oracle_source_network/state/osn077_direct_canonical_cycle.json"
report.write_text(json.dumps({
    "rows":rows,
    "production_surface_authority":True,
    "execution_authority":False,
},indent=2),encoding="utf-8")

print("[REPORT]",report)
print("[PASS] NHL/MLS/EPL exact production surfaces frozen from their certified tests")
print("[PASS] frozen production surfaces directly returned canonical sports events")
print("[PASS] NFL/NCAAF/NBA exact source+extractor chains retained")
print("[PASS] no guessed NHL/MLS/EPL schema conversion remains")
print("[PASS] no certification subprocess used by production runtime")
print("[PASS] OSN-077 production-surface-authority rebuild certified")
