from pathlib import Path
import json,hashlib,shutil
ROOT=Path.cwd()
S097=ROOT/"qseries_v2/oracle_source_network/state/osn097_native_sports_health_contract.json"
WRAP=ROOT/"run_oracle_live_WITH_OSN_SPORTS.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn098_temporary_wrapper_retirement.json"
TEST=ROOT/"test_osn_098_temporary_sports_wrapper_retirement_REPAIR.py"
def main():
    print("="*120);print(" OSN-098 TEMPORARY SPORTS WRAPPER RETIREMENT — REPAIR");print("="*120)
    if not S097.exists():raise SystemExit("[FAIL] missing repaired OSN-097 state")
    retired=None
    if WRAP.exists():
        h=hashlib.sha256(WRAP.read_bytes()).hexdigest()
        d=ROOT/"qseries_v2/oracle_source_network/retired";d.mkdir(parents=True,exist_ok=True)
        retired=d/("run_oracle_live_WITH_OSN_SPORTS_retired_"+h[:16]+".py")
        if retired.exists():WRAP.unlink()
        else:shutil.move(str(WRAP),str(retired))
        print("[RETIRED]",retired.relative_to(ROOT))
    else:
        print("[PASS] temporary wrapper already absent")
    state={"wrapper":"run_oracle_live_WITH_OSN_SPORTS.py","active":False,
           "retired_path":str(retired.relative_to(ROOT)) if retired else None,
           "production_launcher":"run_oracle_LIVE.py","execution_authority":False}
    STATE.write_text(json.dumps(state,indent=2),encoding="utf-8")
    TEST.write_text("""from pathlib import Path\nimport json\nr=Path('.')\nd=json.loads((r/'qseries_v2/oracle_source_network/state/osn098_temporary_wrapper_retirement.json').read_text())\nassert not (r/'run_oracle_live_WITH_OSN_SPORTS.py').exists()\nassert d['active'] is False and d['production_launcher']=='run_oracle_LIVE.py'\nassert d['execution_authority'] is False\nprint('[PASS] temporary sports wrapper retired/absent')\nprint('[PASS] run_oracle_LIVE.py is sole production launcher')\nprint('[PASS] OSN-098 repair certified')\n""",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT));print("[WRITE]",TEST.name)
    print("[PASS] run_oracle_LIVE.py remains production launcher")
if __name__=="__main__":main()
