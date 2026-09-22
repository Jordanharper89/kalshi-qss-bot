
from pathlib import Path
import ast,json,hashlib
ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn076_production_surface_foundation.json"
d=json.loads(STATE.read_text(encoding="utf-8"))
assert [x["league"] for x in d["rows"]]==["NHL","MLS","EPL"]
for r in d["rows"]:
    p=ROOT/r["promoted_path"]
    tree=ast.parse(p.read_text(encoding="utf-8"))
    calls=False
    for n in ast.walk(tree):
        if isinstance(n,ast.Call):
            f=n.func
            calls |= isinstance(f,ast.Name) and f.id=="CanonicalSportsEvent"
            calls |= isinstance(f,ast.Attribute) and f.attr=="CanonicalSportsEvent"
    assert calls, r
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r["sha256"]
    print(f"[FOUNDATION] {r['league']} executable_source={r['source_path']} promoted={r['promoted_path']}")
assert d["execution_authority"] is False
print("[PASS] all promoted production surfaces contain executable canonical-event construction")
print("[PASS] OSN-076 executable-constructor foundation rebuild certified")
