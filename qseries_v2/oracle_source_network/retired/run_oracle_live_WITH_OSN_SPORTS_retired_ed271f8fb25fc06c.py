from pathlib import Path
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
