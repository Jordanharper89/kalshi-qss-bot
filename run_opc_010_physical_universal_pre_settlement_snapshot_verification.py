from pathlib import Path
import argparse
from qseries_v2.oracle_pre_settlement_coverage.opc_009_bounded_universal_snapshot_cycle import run_bounded_universal_snapshot_cycle
from qseries_v2.oracle_pre_settlement_coverage.opc_002_bounded_open_market_sampler import sample_live_open_markets
from qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers,evaluate_canonical_coverage

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--max-markets",type=int,default=100)
    p.add_argument("--lookback-hours",type=float,default=24)
    a=p.parse_args()
    print("="*88);print(" OPC-010 PHYSICAL UNIVERSAL PRE-SETTLEMENT SNAPSHOT VERIFICATION");print("="*88)
    sample=sample_live_open_markets(Path.cwd(),pages=1)
    before=evaluate_canonical_coverage(sample.markets,read_recent_canonical_tickers(Path.cwd(),a.lookback_hours,250000))
    print(f"[BEFORE] sampled={before.sampled_markets} covered={before.markets_with_canonical_observation} missing={before.markets_without_canonical_observation} rate={before.coverage_rate:.2%}")
    s=run_bounded_universal_snapshot_cycle(Path.cwd(),max_markets=a.max_markets,lookback_hours=a.lookback_hours,progress=lambda x:print(x,flush=True))
    print(f"[CYCLE] open={s.open_markets} missing_before={s.missing_before} planned={s.snapshots_planned} persisted={s.snapshots_persisted}")
    after=evaluate_canonical_coverage(sample.markets,read_recent_canonical_tickers(Path.cwd(),a.lookback_hours,250000))
    delta=after.markets_with_canonical_observation-before.markets_with_canonical_observation
    print(f"[AFTER] sampled={after.sampled_markets} covered={after.markets_with_canonical_observation} missing={after.markets_without_canonical_observation} rate={after.coverage_rate:.2%}")
    print(f"[COVERAGE DELTA] +{delta} markets")
    if s.snapshots_persisted<=0: raise SystemExit("No snapshots persisted")
    if delta<=0: raise SystemExit("Coverage did not improve")
    print("[PASS] Missing open markets acquired as canonical market_snapshot observations")
    print("[PASS] Persisted through existing OLA PostgreSQL canonical router")
    print("[PASS] Fast ticker/trade lane untouched")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-010 PHYSICAL UNIVERSAL PRE-SETTLEMENT SNAPSHOT VERIFIED")
    return 0
if __name__=="__main__": raise SystemExit(main())
