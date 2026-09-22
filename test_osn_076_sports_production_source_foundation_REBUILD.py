
from pathlib import Path
import json, hashlib

ROOT=Path.cwd()
state=ROOT/"qseries_v2/oracle_source_network/state/osn076_production_surface_foundation.json"
assert state.exists()
data=json.loads(state.read_text(encoding="utf-8"))
assert [x["league"] for x in data["rows"]]==["NHL","MLS","EPL"]
for r in data["rows"]:
    src=ROOT/r["source_path"]
    dst=ROOT/r["promoted_path"]
    assert src.exists() and dst.exists()
    assert src.read_bytes()==dst.read_bytes()
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==r["source_sha256"]
    compile(dst.read_text(encoding="utf-8"),str(dst),"exec")
    print(f"[FOUNDATION] {r['league']} source={r['source_path']} promoted={r['promoted_path']} sha256={r['source_sha256']}")
assert data["execution_authority"] is False
print("[PASS] byte-exact production-source promotion verified")
print("[PASS] OSN-076 sports production source foundation rebuilt")
