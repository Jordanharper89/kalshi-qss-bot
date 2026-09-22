
from pathlib import Path
ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_source_network/certification/bounded_dual_runtime_physical_gate.py"
STATE=ROOT/"qseries_v2/oracle_source_network/state/osn089_bounded_dual_runtime_physical_gate.json"
TEST=ROOT/"test_osn_089_bounded_dual_runtime_physical_gate.py"
MODULE="""from pathlib import Path
import subprocess,sys,time,json
def run_gate(root=None):
    base=Path(root or Path.cwd()).resolve()
    cfg=json.loads((base/'qseries_v2/oracle_source_network/state/osn086_production_launcher_contract.json').read_text())
    launcher=base/cfg['launcher_path']
    bp=subprocess.Popen([sys.executable,str(launcher)],cwd=str(base),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        time.sleep(5)
        base_alive=(bp.poll() is None)
        code='from pathlib import Path; from qseries_v2.oracle_source_network.runtime.sports_supervised_child import run_once; run_once(Path.cwd(),15,45.0)'
        sp=subprocess.run([sys.executable,'-c',code],cwd=str(base),timeout=90)
        if sp.returncode!=0: raise RuntimeError('sports child failed rc='+str(sp.returncode))
        return {'base_launcher_boot_alive':base_alive,'sports_cycle_completed':True,'execution_authority':False}
    finally:
        if bp.poll() is None:
            bp.terminate()
            try: bp.wait(timeout=10)
            except subprocess.TimeoutExpired: bp.kill()
"""
def main():
    print("="*120); print(" OSN-089 BOUNDED DUAL-RUNTIME PHYSICAL GATE"); print("="*120)
    dep=ROOT/"qseries_v2/oracle_source_network/state/osn088_extension_supervisor.json"
    if not dep.exists(): raise SystemExit("[FAIL] missing dependency: "+str(dep.relative_to(ROOT)))
    TARGET.parent.mkdir(parents=True,exist_ok=True); TARGET.write_text(MODULE,encoding="utf-8"); compile(MODULE,str(TARGET),"exec")
    TEST.write_text("""from pathlib import Path
import json
from qseries_v2.oracle_source_network.certification.bounded_dual_runtime_physical_gate import run_gate
r=run_gate(Path.cwd()); print('[DUAL_RUNTIME_GATE]',r)
assert r['base_launcher_boot_alive'] is True
assert r['sports_cycle_completed'] is True
p=Path.cwd()/'qseries_v2/oracle_source_network/state/osn089_bounded_dual_runtime_physical_gate.json'
p.write_text(json.dumps(r,indent=2),encoding='utf-8')
print('[STATE]',p)
print('[PASS] OSN-089 bounded dual-runtime physical gate certified')
""",encoding="utf-8")
    print("[WRITE]",TARGET.relative_to(ROOT)); print("[WRITE]",TEST.name); print("[PASS] execution_authority=FALSE")
if __name__=="__main__": main()
