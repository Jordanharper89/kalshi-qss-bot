from pathlib import Path
import argparse
from qseries_v2.oracle_adapters.kalshi.oad_038_persistent_persistence_bridge import run_kalshi_persistence_bridge

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--max-persisted",type=int,default=None)
    a=p.parse_args()
    print("="*72,flush=True)
    print(" OAD-038 KALSHI → OLA → POSTGRESQL LIVE BRIDGE",flush=True)
    print("="*72,flush=True)
    print("[MODE] "+("PRODUCTION 24/7 — UNBOUNDED" if a.max_persisted is None else f"DIAGNOSTIC — max_persisted={a.max_persisted}"),flush=True)
    try:
        r=run_kalshi_persistence_bridge(Path.cwd(),max_persisted=a.max_persisted,progress=lambda x:print(x,flush=True))
        print("[SUMMARY]",r,flush=True)
        return 0
    except KeyboardInterrupt:
        print("\\n[STOP] Kalshi persistence bridge stopped by operator.",flush=True)
        return 0
if __name__=="__main__": raise SystemExit(main())
