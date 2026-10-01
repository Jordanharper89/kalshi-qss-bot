from pathlib import Path
import json,hashlib,datetime,ast
R=Path.cwd()
O=R/"qseries_v2/oracle_learning_runtime/olr_009_high_coverage_learning_cycle.py"
M=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/slop_075b_ast_crash_safe_same_writer_cutover.py"
assert O.exists() and M.exists(); ast.parse(O.read_text(encoding="utf-8")); ast.parse(M.read_text(encoding="utf-8"))
F=R/"runtime_state/solana_live_opportunity/slop_078b_buy_pressure_reference_freeze.json"; F.parent.mkdir(parents=True,exist_ok=True)
d={"revision":"SLOP_078B_BUY_PRESSURE_REFERENCE_FREEZE","frozen_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"thesis":{"condition":"BUY_PRESSURE","horizon_seconds":60,"target_fraction":0.10,"stop_fraction":-0.05,"friction_bps":200},
"olr009_sha256":hashlib.sha256(O.read_bytes()).hexdigest(),"cutover_sha256":hashlib.sha256(M.read_bytes()).hexdigest(),"execution_authority":False}
F.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
T=R/"test_slop_078b_buy_pressure_reference_freeze.py"
T.write_text("""from pathlib import Path
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
""",encoding="utf-8")
print("[PASS] SLOP-078B BUY_PRESSURE reference freeze installed")
print("[PASS] test installed:",T.name)
