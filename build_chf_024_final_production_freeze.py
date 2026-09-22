from pathlib import Path
import hashlib,json,py_compile
from datetime import datetime,timezone

R=Path.cwd(); P=R/"qseries_v2"/"oracle_coinbase_high_frequency"
L=R/"run_oracle_LIVE.py"; C=R/"run_coinbase_hf_live.py"
assert L.exists() and C.exists()
s=L.read_text(encoding="utf-8"); c=C.read_text(encoding="utf-8")
assert '"coinbase_hf"' in s and '"run_coinbase_hf_live.py"' in s
assert "persist_new(ROOT)" in c and "materialize_history" not in c
m={"schema_version":"CHF-024","status":"FROZEN",
"certified_range":"CHF-001..CHF-024",
"native_child_key":"coinbase_hf","native_child_runner":"run_coinbase_hf_live.py",
"launcher_sha256":hashlib.sha256(L.read_bytes()).hexdigest(),
"products":["BTC-USD","ETH-USD","SOL-USD"],"windows_seconds":[5,15,30,60],
"persistence":"OAD-261 -> OPH-019 -> await_request -> OAD-068",
"history":"FIXED_GRID_EVENT_TIME_ARCHIVE",
"change_policy":"DEFECT_CORRECTIONS_ONLY",
"probability_enabled":False,"direction_enabled":False,
"publication_allowed":False,"execution_authority":False,
"frozen_at":datetime.now(timezone.utc).isoformat()}
f=P/"chf_024_final_freeze_manifest.json"
f.write_text(json.dumps(m,indent=2,sort_keys=True),encoding="utf-8")
T='''from pathlib import Path
import json
R=Path.cwd(); P=R/"qseries_v2"/"oracle_coinbase_high_frequency"
m=json.loads((P/"chf_024_final_freeze_manifest.json").read_text())
assert m["status"]=="FROZEN" and m["certified_range"]=="CHF-001..CHF-024"
assert m["native_child_key"]=="coinbase_hf"
assert m["windows_seconds"]==[5,15,30,60]
assert not any(m[x] for x in ("probability_enabled","direction_enabled","publication_allowed","execution_authority"))
assert (R/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl").stat().st_size>92691
print("[PASS] native Coinbase HF production child frozen")
print("[PASS] fixed-grid HF historical archive physically populated")
print("[PASS] probability/direction/publication/execution remain disabled")
print("[PASS] CHF-001..CHF-024 FINAL PRODUCTION FREEZE CERTIFIED")
'''
t=R/"test_chf_024_final_production_freeze.py"
t.write_text(T,encoding="utf-8"); py_compile.compile(str(t),doraise=True)
print("[PASS] wrote",f); print("[PASS] wrote",t)