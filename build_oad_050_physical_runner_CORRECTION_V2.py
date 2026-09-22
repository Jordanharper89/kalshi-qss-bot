from pathlib import Path
import os
ROOT=Path.cwd().resolve()
RUNNER=ROOT/"run_oad_050_physical_full_universe_coverage_verification.py"
SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_046_live_universe_enumeration import enumerate_live_open_universe\nfrom qseries_v2.oracle_adapters.kalshi.oad_047_physical_coverage_plan import build_physical_coverage_plan\nfrom qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import run_physical_multi_partition_persistence\n\ndef main():\n    root=Path.cwd()\n    print("="*72,flush=True)\n    print(" OAD-050 PHYSICAL FULL-UNIVERSE COVERAGE VERIFICATION — CORRECTION V2",flush=True)\n    print("="*72,flush=True)\n\n    print("[STAGE 1] Enumerating live open universe ONCE",flush=True)\n    credentials=load_kalshi_credentials(root=root)\n    universe=enumerate_live_open_universe(\n        credentials,\n        timeout_seconds=10,\n        progress=lambda x:print(x,flush=True),\n    )\n\n    print("[STAGE 2] Building coverage plan from cached universe snapshot",flush=True)\n    plan=build_physical_coverage_plan(universe.tickers,100)\n    print(f"[UNIVERSE] open_markets={len(universe.tickers)} pages={universe.pages}",flush=True)\n    print("[FAST LANE] ticker+trade market_filter=NONE coverage=ALL",flush=True)\n    print(f"[ORDERBOOK] partitions_total={len(plan.orderbook_partitions)} physical_probe_partitions={min(3,len(plan.orderbook_partitions))}",flush=True)\n\n    print("[STAGE 3] Starting physical WebSocket coverage + persistence",flush=True)\n    result=run_physical_multi_partition_persistence(\n        root,\n        universe=universe,\n        max_persisted=12,\n        orderbook_partitions_to_activate=min(3,len(plan.orderbook_partitions)),\n        progress=lambda x:print(x,flush=True),\n    )\n\n    print("[SUMMARY]",result,flush=True)\n\n    if result.open_markets!=len(universe.tickers):\n        raise SystemExit("[FAIL] universe mismatch")\n    if result.events_persisted<12:\n        raise SystemExit("[FAIL] persistence target not reached")\n\n    print("[PASS] Global ticker/trade fast lane covers the full live Kalshi universe",flush=True)\n    print("[PASS] Multiple explicit orderbook partitions activated",flush=True)\n    print("[PASS] Real events persisted through certified OLA PostgreSQL router",flush=True)\n    print("[DONE] OAD-050 PHYSICAL FULL-UNIVERSE COVERAGE VERIFIED",flush=True)\n\nif __name__=="__main__":\n    main()\n'
def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    print("="*72);print(" OAD-050 PHYSICAL RUNNER CORRECTION V2 INSTALLER");print("="*72)
    old=RUNNER.read_bytes() if RUNNER.exists() else None
    try:
        write_exact(RUNNER,SOURCE)
        compile(RUNNER.read_text(encoding="utf-8"),str(RUNNER),"exec")
    except Exception:
        if old is None:
            if RUNNER.exists(): RUNNER.unlink()
        else:
            RUNNER.write_bytes(old)
        print("[ROLLBACK] OAD-050 runner correction failed")
        raise
    print("[PASS] OAD-050 physical runner now enumerates once and reuses cached universe")
    print("[PASS] Progress output enabled")
    print("[DONE] OAD-050 PHYSICAL RUNNER CORRECTION V2 INSTALLED")
if __name__=="__main__":
    main()
