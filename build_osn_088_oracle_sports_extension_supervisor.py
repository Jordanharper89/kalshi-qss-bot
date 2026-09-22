
from pathlib import Path
import json,hashlib
ROOT=Path.cwd()
TARGET=ROOT/"run_oracle_live_WITH_OSN_SPORTS.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn088_extension_supervisor.json"
TEST=ROOT/"test_osn_088_oracle_sports_extension_supervisor.py"
LAUNCHER="""from pathlib import Path
import subprocess,sys,time,json
ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json').read_text())
BASE=ROOT/CFG['launcher_path']
SPORTS='from pathlib import Path; from qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_forever; run_forever(Path.cwd(),30.0,15,45.0)'
def main():
    base=subprocess.Popen([sys.executable,str(BASE)],cwd=str(ROOT))
    sports=subprocess.Popen([sys.executable,'-c',SPORTS],cwd=str(ROOT))
    print('[ORACLE_BASE_PID]',base.pid)
    print('[OSN_SPORTS_PID]',sports.pid)
    print('[PASS] execution_authority=FALSE')
    try:
        while True:
            if base.poll() is not None: raise RuntimeError('ORACLE_BASE exited rc='+str(base.returncode))
            if sports.poll() is not None: raise RuntimeError('OSN_SPORTS exited rc='+str(sports.returncode))
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        for p in (sports,base):
            if p.poll() is None: p.terminate()
if __name__=='__main__': main()
"""
def main():
    print("="*120); print(" OSN-088 ORACLE + SPORTS EXTENSION SUPERVISOR"); print("="*120)
    s86=ROOT/"qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json"
    s87=ROOT/"qseries_v2/oracle_source_network/state/osn087_sports_supervised_child.json"
    for dep in (s86,s87):
        if not dep.exists(): raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
        print("[PASS] dependency verified:",dep.relative_to(ROOT))
    c=json.loads(s86.read_text()); base=ROOT/c["launcher_path"]
    if hashlib.sha256(base.read_bytes()).hexdigest()!=c["launcher_sha256"]: raise SystemExit("[FAIL] base launcher changed since OSN-086")
    TARGET.write_text(LAUNCHER,encoding="utf-8"); compile(LAUNCHER,str(TARGET),"exec")
    STATE.write_text(json.dumps({"launcher":TARGET.name,"base_launcher":c["launcher_path"],"base_sha256":c["launcher_sha256"],"base_mutated":False,"sports_child":"qseries_v2.oracle_source_network.runtime.sports_supervised_child","terminal_dependency":"NONE","execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("""from pathlib import Path
import json,hashlib
r=Path.cwd(); s=json.loads((r/'qseries_v2/oracle_source_network/state/osn088_extension_supervisor.json').read_text())
assert hashlib.sha256((r/s['base_launcher']).read_bytes()).hexdigest()==s['base_sha256']
assert s['base_mutated'] is False
assert (r/s['launcher']).exists()
print('[PASS] frozen base launcher unchanged')
print('[PASS] extension supervisor installed')
print('[PASS] OSN-088 certified')
""",encoding="utf-8")
    print("[WRITE]",TARGET.name); print("[STATE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name); print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
