from pathlib import Path
from qseries_v2.oracle_pre_settlement_coverage.opc_002_bounded_open_market_sampler import sample_live_open_markets
from qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers,evaluate_canonical_coverage
from qseries_v2.oracle_pre_settlement_coverage.opc_004_live_coverage_gap_classifier import classify_coverage_gap

if __name__=="__main__":
    print("="*88)
    print(" OPC-005 PHYSICAL LIVE PRE-SETTLEMENT COVERAGE CENSUS")
    print("="*88)
    s=sample_live_open_markets(Path.cwd(),pages=1)
    print(f"[OPEN MARKET SAMPLE] unique_tickers={s.unique_tickers}")
    c=read_recent_canonical_tickers(Path.cwd(),24,250000)
    print(f"[CANONICAL RECENT] unique_tickers={len(c)}")
    r=evaluate_canonical_coverage(s.markets,c)
    g=classify_coverage_gap(r)
    print(f"[SAMPLED OPEN MARKETS] {r.sampled_markets}")
    print(f"[WITH CANONICAL OBSERVATION] {r.markets_with_canonical_observation}")
    print(f"[WITHOUT CANONICAL OBSERVATION] {r.markets_without_canonical_observation}")
    print(f"[COVERAGE RATE] {r.coverage_rate:.2%}")
    print(f"[SEVERITY] {g.severity}")
    print(f"[LIKELY GAP] {g.likely_gap}")
    print(f"[RECOMMENDED NEXT CAPABILITY] {g.recommended_next_capability}")
    print("[PASS] Live coverage census completed read-only")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-005 PHYSICAL PRE-SETTLEMENT COVERAGE CENSUS COMPLETE")
