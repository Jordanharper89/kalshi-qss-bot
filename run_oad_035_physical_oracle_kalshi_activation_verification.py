from pathlib import Path
from qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import run_persistent_kalshi_loop
from qseries_v2.oracle_adapters.kalshi.oad_033_persistence_verification import run_existing_persistence_diagnostic
from qseries_v2.oracle_adapters.kalshi.oad_034_runtime_status import build_oracle_kalshi_status

def main():
    root=Path.cwd()
    print("="*72,flush=True)
    print(" OAD-035 PHYSICAL ORACLE + KALSHI ACTIVATION VERIFICATION",flush=True)
    print("="*72,flush=True)
    print("[FAST LANE] Waiting for real Kalshi market events",flush=True)
    ws=run_persistent_kalshi_loop(root,stop_after_market_messages=3,timeout_seconds=15,progress=lambda x:print(x,flush=True))
    print("[PERSISTENCE LANE] Running existing certified OLA/PostgreSQL diagnostic",flush=True)
    code,persisted,out=run_existing_persistence_diagnostic(root,timeout_seconds=180)
    print(out,flush=True)
    status=build_oracle_kalshi_status(True,ws.subscription_acks>0,ws.market_messages,ws.reconnects,persisted)
    print("[STATUS]",status,flush=True)
    if status.status!="LIVE_READY":
        raise SystemExit("[FAIL] Oracle/Kalshi physical activation did not reach LIVE_READY")
    print("[PASS] Real Kalshi market events observed and canonical Live Shadow/PostgreSQL persistence advanced",flush=True)
    print("[PASS] Dual-lane Oracle/Kalshi production activation verified",flush=True)
    print("[DONE] OAD-035 PHYSICAL ACTIVATION VERIFIED",flush=True)

if __name__=="__main__":
    main()
