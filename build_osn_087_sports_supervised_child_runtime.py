
from pathlib import Path
import json
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_source_network/runtime/sports_supervised_child.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn087_sports_supervised_child.json"
TEST=ROOT/"test_osn_087_sports_supervised_child_runtime.py"
MODULE="""from pathlib import Path
from datetime import datetime, timezone
import json,time
from qseries_v2.oracle_source_network.runtime.six_league_durable_runtime_cycle import run_cycle
HEARTBEAT='qseries_v2/oracle_source_network/state/osn087_sports_child_heartbeat.json'
def _beat(root,status,cycles,error=None):
    p=Path(root)/HEARTBEAT
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({'status':status,'cycles':cycles,'last_heartbeat':datetime.now(timezone.utc).isoformat(),'last_error':error,'terminal_dependency':'NONE','execution_authority':False},indent=2),encoding='utf-8')
def run_once(root=None,timeout=15,commit_timeout_seconds=45.0):
    base=Path(root or Path.cwd()).resolve()
    rows,state=run_cycle(root=base,timeout=timeout,commit_timeout_seconds=commit_timeout_seconds)
    _beat(base,'HEALTHY',1,None)
    return rows,state
def run_forever(root=None,cadence_seconds=30.0,timeout=15,commit_timeout_seconds=45.0,max_cycles=None):
    base=Path(root or Path.cwd()).resolve(); cycles=0
    while True:
        rows,state=run_cycle(root=base,timeout=timeout,commit_timeout_seconds=commit_timeout_seconds)
        cycles+=1; _beat(base,'HEALTHY',cycles,None)
        if max_cycles is not None and cycles>=max_cycles: return cycles
        time.sleep(max(1.0,float(cadence_seconds)))
"""
def main():
    print("="*120); print(" OSN-087 SPORTS SUPERVISED CHILD RUNTIME"); print("="*120)
    for dep in (
        ROOT/"qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json",
        ROOT/"qseries_v2/oracle_source_network/runtime/six_league_durable_runtime_cycle.py",
        ROOT/"qseries_v2/oracle_source_network/state/osn085_durable_runtime_cycle.json"):
        if not dep.exists(): raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))
    TARGET.write_text(MODULE,encoding="utf-8"); compile(MODULE,str(TARGET),"exec")
    STATE.write_text(json.dumps({"entrypoint":"qseries_v2.oracle_source_network.runtime.sports_supervised_child:run_forever","cadence_seconds":30,"terminal_dependency":"NONE","execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("""from pathlib import Path
from qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_once
rows,state=run_once(Path.cwd(),15,45.0)
assert len(rows)==6
assert all(x.readback_count>0 and x.checkpoint_written for x in rows)
print('[PASS] six-league supervised child bounded cycle certified')
print('[PASS] OSN-087 certified')
""",encoding="utf-8")
    print("[WRITE]",TARGET.relative_to(ROOT)); print("[STATE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name); print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
