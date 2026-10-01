from pathlib import Path
import json
R=Path.cwd(); p=R/"runtime_state/solana_live_opportunity/slop_078b_buy_pressure_reference_freeze.json"
d=json.loads(p.read_text(encoding="utf-8")); t=d["thesis"]
assert t["condition"]=="BUY_PRESSURE" and t["horizon_seconds"]==60
assert t["target_fraction"]==0.10 and t["stop_fraction"]==-0.05 and t["friction_bps"]==200
assert d["execution_authority"] is False
print("[PASS] BUY_PRESSURE prospective learning reference frozen")
print("[PASS] economics preserved: 60s +10%/-5% 200bps")
print("[PASS] SLOP-078B CERTIFIED execution_authority=FALSE")
print("[NEXT] OOI-001 ORACLE OPPORTUNITY INTELLIGENCE")
