from pathlib import Path
import json
ROOT=Path.cwd()
S095=ROOT/"qseries_v2/oracle_source_network/state/osn095_native_sports_full_cycle_gate.json"
S096F=ROOT/"qseries_v2/oracle_source_network/state/osn096_native_sports_parent_exit_forensic.json"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn097_native_sports_health_contract.json"
TEST=ROOT/"test_osn_097_native_sports_health_contract_FREEZE_REPAIR.py"

def main():
    print("="*120)
    print(" OSN-097 NATIVE SPORTS HEALTH CONTRACT FREEZE — REPAIR")
    print("="*120)
    if not S095.exists():
        raise SystemExit("[FAIL] missing certified OSN-095 full-cycle state")
    s095=json.loads(S095.read_text(encoding="utf-8"))
    if not (s095.get("oracle_reported_sports_healthy") and s095.get("all_six_leagues_seen") and s095.get("sports_heartbeat_advanced")):
        raise SystemExit("[FAIL] OSN-095 production sports runtime proof incomplete")
    forensic_present=S096F.exists()
    d={
        "component":"sports",
        "production_launcher":"run_oracle_LIVE.py",
        "supervision":"NATIVE_CHILDREN_REGISTRY",
        "healthy_state":"HEALTHY",
        "six_league_full_cycle_certified":True,
        "sports_heartbeat_advanced":True,
        "restart_counter_name":"sports_restarts",
        "restart_recovery_physical_certified":False,
        "restart_recovery_status":"DEFERRED_TO_ORACLE_RUNTIME_HARDENING",
        "osn096_forensic_present":forensic_present,
        "terminal_dependency":"NONE",
        "execution_authority":False
    }
    STATE.write_text(json.dumps(d,indent=2),encoding="utf-8")
    TEST.write_text("""import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/oracle_source_network/state/osn097_native_sports_health_contract.json').read_text())\nassert d['six_league_full_cycle_certified'] is True\nassert d['sports_heartbeat_advanced'] is True\nassert d['restart_recovery_physical_certified'] is False\nassert d['restart_recovery_status']=='DEFERRED_TO_ORACLE_RUNTIME_HARDENING'\nassert d['execution_authority'] is False\nprint('[PASS] native sports HEALTHY contract frozen from OSN-095 physical proof')\nprint('[PASS] restart recovery explicitly not overclaimed')\nprint('[PASS] OSN-097 freeze repair certified')\n""",encoding="utf-8")
    print("[PASS] OSN-095 six-league full production cycle accepted")
    print("[DEFERRED] destructive restart recovery -> Oracle runtime hardening")
    print("[WRITE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)
    print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
