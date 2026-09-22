from pathlib import Path
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
