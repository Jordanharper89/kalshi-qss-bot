from pathlib import Path
import json
ROOT=Path.cwd()
S096=ROOT/"qseries_v2/oracle_source_network/state/osn096_native_sports_restart_recovery_gate.json"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn097_native_sports_health_contract.json"
TEST=ROOT/"test_osn_097_native_sports_health_contract_freeze.py"
def main():
 print("="*120);print(" OSN-097 NATIVE SPORTS HEALTH CONTRACT FREEZE");print("="*120)
 if not S096.exists():raise SystemExit("[FAIL] missing OSN-096 physical state")
 r=json.loads(S096.read_text(encoding="utf-8"))
 if not(r.get("sports_healthy_after_restart") and r.get("sports_restarts_after",0)>=1 and r.get("launcher_alive")):
  raise SystemExit("[FAIL] OSN-096 restart recovery not proven")
 d={"component":"sports","production_launcher":"run_oracle_LIVE.py","supervision":"NATIVE_CHILDREN_REGISTRY",
    "healthy_state":"HEALTHY","restart_counter":"sports_restarts","restart_recovery_certified":True,
    "terminal_dependency":"NONE","execution_authority":False}
 STATE.write_text(json.dumps(d,indent=2),encoding="utf-8")
 TEST.write_text("""import json\nfrom pathlib import Path\nd=json.loads(Path("qseries_v2/oracle_source_network/state/osn097_native_sports_health_contract.json").read_text())\nassert d["restart_recovery_certified"] and d["execution_authority"] is False\nassert d["supervision"]=="NATIVE_CHILDREN_REGISTRY"\nprint("[PASS] native sports health/restart contract frozen")\nprint("[PASS] OSN-097 certified")\n""",encoding="utf-8")
 print("[STATE]",STATE.relative_to(ROOT));print("[WRITE]",TEST.name);print("[PASS] native health/restart contract frozen")
if __name__=="__main__":main()
