from __future__ import annotations
import argparse,subprocess,sys,time
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");p.add_argument("--cadence-seconds",type=float,default=5.0);a=p.parse_args(argv);root=Path.cwd()
 print("="*72,flush=True);print(" OLR-035 LEARNING + CALIBRATION SUPERVISOR",flush=True);print("="*72,flush=True)
 if a.check:
  from qseries_v2.oracle_learning_runtime.olr_035_production_calibration_supervision_gate import verify_olr_035_production_calibration_supervision_gate
  ok=verify_olr_035_production_calibration_supervision_gate() and (root/"run_olr_034_continuous_calibration_ingestion.py").is_file();print("[READY] learning + calibration supervisor verified" if ok else "[ERROR] supervisor verification failed");return 0 if ok else 1
 cmds={"learning":[sys.executable,"-c","from qseries_v2.oracle_learning_runtime.olr_010_runtime import main; raise SystemExit(main())"],"calibration":[sys.executable,str(root/"run_olr_034_continuous_calibration_ingestion.py")]}
 children={k:subprocess.Popen(v,cwd=str(root)) for k,v in cmds.items()};restarts={k:0 for k in cmds};hb=0
 try:
  while True:
   hb+=1
   for k,p0 in tuple(children.items()):
    if p0.poll() is not None:restarts[k]+=1;children[k]=subprocess.Popen(cmds[k],cwd=str(root))
   print(f"[OLR] heartbeat={hb} learning={'RUNNING' if children['learning'].poll() is None else 'STOPPED'} calibration={'RUNNING' if children['calibration'].poll() is None else 'STOPPED'} learning_restarts={restarts['learning']} calibration_restarts={restarts['calibration']} execution_authority=FALSE",flush=True);time.sleep(a.cadence_seconds)
 except KeyboardInterrupt:
  for p0 in children.values():
   if p0.poll() is None:p0.terminate()
  return 0
if __name__=="__main__":raise SystemExit(main())
