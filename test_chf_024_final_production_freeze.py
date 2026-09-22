from pathlib import Path
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
