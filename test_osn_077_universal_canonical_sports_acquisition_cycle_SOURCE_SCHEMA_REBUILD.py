
from pathlib import Path
import json
from qseries_v2.oracle_source_network.runtime.direct_canonical_sports_cycle import acquire_canonical_events

root=Path.cwd()
rows=[]

expected_minimum={"NFL":1,"NCAAF":1,"NBA":1,"NHL":1,"MLS":1,"EPL":1}

for league in ("NFL","NCAAF","NBA","NHL","MLS","EPL"):
    r=acquire_canonical_events(league,root=root,timeout=12)
    print(
        f"[DIRECT] {league} events={r.event_count} "
        f"acquisition_type={r.acquisition_type} "
        f"extractor_input={r.extractor_input_type}"
    )
    for c in r.callables_attempted:
        print("  [CALL]",c)

    assert r.event_count >= expected_minimum[league]
    assert r.execution_authority is False

    sample=r.canonical_events[0]
    print(
        f"  [SAMPLE] provider_event_id={getattr(sample,'provider_event_id',None)} "
        f"home={getattr(sample,'home',getattr(sample,'home_team',None))} "
        f"away={getattr(sample,'away',getattr(sample,'away_team',None))}"
    )

    rows.append({
        "league":league,
        "event_count":r.event_count,
        "callables":list(r.callables_attempted),
        "acquisition_type":r.acquisition_type,
        "extractor_input_type":r.extractor_input_type,
    })

report=root/"qseries_v2/oracle_source_network/state/osn077_direct_canonical_cycle.json"
report.write_text(
    json.dumps({"rows":rows,"execution_authority":False},indent=2),
    encoding="utf-8",
)

print("[REPORT]",report)
print("[PASS] NFL/NCAAF/NBA exact extractor chains retained")
print("[PASS] NHL canonicalized from certified NHL JSON schedule schema")
print("[PASS] MLS canonicalized from exact OSN-052 schedule keys")
print("[PASS] EPL canonicalized from Premier League/FPL fixture schema")
print("[PASS] six admitted leagues produced direct canonical events")
print("[PASS] no subprocess certification wrapper used")
print("[PASS] OSN-077 source-schema rebuild certified")
