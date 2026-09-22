from pathlib import Path
import argparse,time
from qseries_v2.oracle_learning_runtime.olr_034_supervised_continuous_calibration_runtime import run_calibration_runtime_cycle,is_transient_calibration_error
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--settled-limit",type=int,default=100);p.add_argument("--evidence-limit",type=int,default=25);p.add_argument("--cadence-seconds",type=float,default=30.0);p.add_argument("--once",action="store_true");a=p.parse_args(argv)
 root=Path.cwd();print("="*72,flush=True);print(" OLR-034 CONTINUOUS CALIBRATION INGESTION RUNTIME",flush=True);print("="*72,flush=True);fails=0
 while True:
  try:
   c=run_calibration_runtime_cycle(root,a.settled_limit,a.evidence_limit);i=c.ingestion;s=c.state;f=c.feedback
   print(f"[CALIBRATION] cycle={s.cycles_completed} settled={i.settled_scanned} learned={i.learned_settlements} exact_evidence={i.exact_evidence_matches} candidates={i.candidates} admitted={i.admitted} duplicates={i.duplicate_records} abstentions={i.probability_abstentions} ledger_records={i.ledger_records}",flush=True)
   print(f"[CALIBRATION FEEDBACK] records={f.calibration_records} markets={f.markets} mature_markets={f.mature_markets} execution_authority=FALSE",flush=True);fails=0
   if a.once:return 0
   time.sleep(a.cadence_seconds)
  except KeyboardInterrupt:
   print("\n[STOP] Calibration ingestion runtime stopped by operator.",flush=True);return 0
  except Exception as exc:
   if not is_transient_calibration_error(exc):raise
   fails+=1;delay=min(60.0,2.0**min(fails,5));print(f"[CALIBRATION] transient_error={type(exc).__name__} retry_in={delay:.1f}s",flush=True)
   if a.once:return 2
   time.sleep(delay)
if __name__=="__main__":raise SystemExit(main())
