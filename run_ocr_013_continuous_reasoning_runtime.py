from pathlib import Path
import argparse,time
from qseries_v2.oracle_continuous_reasoning.ocr_013_continuous_reasoning_loop import run_continuous_reasoning_cycle

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--batch-size",type=int,default=50)
    p.add_argument("--cadence-seconds",type=float,default=2.0)
    p.add_argument("--once",action="store_true")
    a=p.parse_args()
    if a.batch_size<1 or a.cadence_seconds<=0:raise SystemExit("invalid runtime arguments")
    root=Path.cwd()
    print("="*72,flush=True);print(" OCR-013 CONTINUOUS MARKET-AWARE REASONING RUNTIME",flush=True);print("="*72,flush=True)
    cycles=0
    try:
        while True:
            s=run_continuous_reasoning_cycle(root,limit=a.batch_size,progress=lambda x:print(x,flush=True))
            cycles+=1
            print(f"[OCR] cycle={cycles} idle={s.idle} rows={s.rows_read} markets_reasoned={s.markets_reasoned}",flush=True)
            if a.once:return 0
            time.sleep(a.cadence_seconds)
    except KeyboardInterrupt:
        print("\\n[STOP] OCR continuous reasoning runtime stopped by operator.",flush=True)
        return 0

if __name__=="__main__":
    raise SystemExit(main())
