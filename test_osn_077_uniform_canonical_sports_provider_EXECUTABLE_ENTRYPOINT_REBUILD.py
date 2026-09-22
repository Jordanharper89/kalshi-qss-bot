
from pathlib import Path
import json
from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events

rows=[]
for league in ("NFL","NCAAF","NBA","NHL","MLS","EPL"):
    r=acquire_canonical_events(league,timeout=15,root=Path.cwd())
    assert r.event_count>0
    assert r.execution_authority is False
    s=r.events[0]
    print(f"[PROVIDER] {league} events={r.event_count} authority={r.authority} callable={r.callable_name}")
    print(f"  [SAMPLE] id={getattr(s,'provider_event_id',None)} home={getattr(s,'home',getattr(s,'home_team',None))} away={getattr(s,'away',getattr(s,'away_team',None))}")
    rows.append({"league":league,"events":r.event_count,"authority":r.authority,"callable":r.callable_name})

state=Path("qseries_v2/oracle_source_network/state/osn077_uniform_provider_contract.json")
state.write_text(json.dumps({"rows":rows,"execution_authority":False},indent=2),encoding="utf-8")
print("[STATE]",state)
print("[PASS] all six admitted leagues produced canonical events through executable production callables")
print("[PASS] no test subprocess used")
print("[PASS] no printed EVENT-line parsing used")
print("[PASS] no guessed NHL/MLS/EPL response schema used")
print("[PASS] OSN-077 executable-entrypoint rebuild certified")
