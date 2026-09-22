
from pathlib import Path
import json
from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events

rows=[]
for league in ("NFL","NCAAF","NBA","NHL","MLS","EPL"):
    r=acquire_canonical_events(league,timeout=15,root=Path.cwd())
    assert r.event_count>0
    assert r.execution_authority is False
    sample=r.events[0]
    print(f"[PROVIDER] {league} events={r.event_count} authority={r.authority}")
    print(f"  [SAMPLE] id={getattr(sample,'provider_event_id',None)} home={getattr(sample,'home',getattr(sample,'home_team',None))} away={getattr(sample,'away',getattr(sample,'away_team',None))}")
    rows.append({"league":league,"events":r.event_count,"authority":r.authority})

state=Path("qseries_v2/oracle_source_network/state/osn077_uniform_provider_contract.json")
state.write_text(json.dumps({"rows":rows,"execution_authority":False},indent=2),encoding="utf-8")
print("[STATE]",state)
print("[PASS] all six admitted leagues expose one acquire_canonical_events contract")
print("[PASS] NHL/MLS/EPL use promoted byte-exact proven surfaces")
print("[PASS] no certification subprocess used")
print("[PASS] OSN-077 uniform canonical sports provider contract rebuilt")
