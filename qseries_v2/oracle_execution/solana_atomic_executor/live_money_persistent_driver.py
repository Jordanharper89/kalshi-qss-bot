from __future__ import annotations
import argparse
import inspect
from . import live_money_driver as d

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=1800.0)
    p.add_argument("--refresh-seconds",type=float,default=60.0)
    a=p.parse_args()
    if a.seconds<300:
        raise RuntimeError("PERSISTENT_SESSION_MINIMUM_300_SECONDS")
    sig=inspect.signature(d._run_generation)
    if len(sig.parameters)!=4:
        raise RuntimeError("LIVE_MONEY_DRIVER_CONTRACT_DRIFT:"+str(sig))
    active={}
    print("[PERSISTENT_MONEY_START] single_startup=True generation=1 warm_session_seconds=%.1f repeated_generation_rebuild=False"%a.seconds,flush=True)
    print("[PERSISTENT_CONTRACT] _run_generation(generation,generation_seconds,refresh_seconds,active)",flush=True)
    print("[PERSISTENT_POLICY] CP24/CP12/templates/websockets=start_once capital_ladder=wallet_funded broadcast=False",flush=True)
    rc,active=d._run_generation(1,float(a.seconds),float(a.refresh_seconds),active)
    print("[PERSISTENT_MONEY_DONE] rc=%s active_pairs=%d"%(str(rc),len(active or {})),flush=True)
    return int(rc or 0)

if __name__=="__main__":
    raise SystemExit(main())
