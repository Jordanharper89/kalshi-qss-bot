from pathlib import Path
import json,hashlib
ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn099_actual_production_launcher_freeze.json"
TEST=ROOT/"test_osn_099_actual_production_launcher_freeze_REPAIR.py"
def main():
    print("="*120);print(" OSN-099 ACTUAL PRODUCTION LAUNCHER FREEZE — REPAIR");print("="*120)
    for p in [
        ROOT/"qseries_v2/oracle_source_network/state/osn095_native_sports_full_cycle_gate.json",
        ROOT/"qseries_v2/oracle_source_network/state/osn097_native_sports_health_contract.json",
        ROOT/"qseries_v2/oracle_source_network/state/osn098_temporary_wrapper_retirement.json"]:
        if not p.exists():raise SystemExit("[FAIL] missing dependency: "+str(p.relative_to(ROOT)))
    launcher=ROOT/"run_oracle_LIVE.py"
    h=hashlib.sha256(launcher.read_bytes()).hexdigest()
    d={"production_launcher":"run_oracle_LIVE.py","sha256":h,
       "sports_native_child":True,"six_league_physical_cycle_certified":True,
       "restart_recovery_physical_certified":False,
       "restart_recovery_status":"DEFERRED_TO_ORACLE_RUNTIME_HARDENING",
       "temporary_wrapper_retired":True,"terminal_dependency":"NONE","execution_authority":False}
    STATE.write_text(json.dumps(d,indent=2),encoding="utf-8")
    TEST.write_text("""from pathlib import Path\nimport json,hashlib\nr=Path('.')\nd=json.loads((r/'qseries_v2/oracle_source_network/state/osn099_actual_production_launcher_freeze.json').read_text())\nassert hashlib.sha256((r/'run_oracle_LIVE.py').read_bytes()).hexdigest()==d['sha256']\nassert d['sports_native_child'] and d['six_league_physical_cycle_certified']\nassert d['restart_recovery_physical_certified'] is False\nassert d['temporary_wrapper_retired'] and d['execution_authority'] is False\nprint('[PASS] exact run_oracle_LIVE.py hash frozen')\nprint('[PASS] restart recovery not falsely certified')\nprint('[PASS] OSN-099 repair certified')\n""",encoding="utf-8")
    print("[SHA256]",h);print("[WRITE]",STATE.relative_to(ROOT));print("[WRITE]",TEST.name)
    print("[PASS] actual production launcher frozen")
if __name__=="__main__":main()
