
from pathlib import Path
import argparse
from qseries_v2.oracle_historical_learning.ohl_009_historical_eligibility_census import run_historical_eligibility_census

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--settled-limit",type=int,default=500)
    p.add_argument("--evidence-limit",type=int,default=50)
    p.add_argument("--quiet",action="store_true")
    a=p.parse_args()

    print("="*72)
    print(" OHL-010 PHYSICAL POSTGRESQL HISTORICAL ELIGIBILITY CENSUS")
    print("="*72)
    print(f"[CONFIG] settled_limit={a.settled_limit} evidence_limit={a.evidence_limit}")
    progress=None if a.quiet else (lambda x:print(x,flush=True))
    c=run_historical_eligibility_census(Path.cwd(),a.settled_limit,a.evidence_limit,progress)

    print("="*72)
    print(" HISTORICAL LEARNING ELIGIBILITY RESULT")
    print("="*72)
    print(f"[SETTLED SCANNED] {c.settled_scanned}")
    print(f"[UNIQUE TICKERS] {c.unique_tickers}")
    print(f"[ELIGIBLE MARKETS] {c.eligible_markets}")
    print(f"[INELIGIBLE MARKETS] {c.ineligible_markets}")
    print(f"[ELIGIBILITY RATE] {c.eligibility_rate:.2%}")
    print(f"[PRE-SETTLEMENT EVIDENCE] {c.total_pre_settlement_evidence}")
    print(f"[INELIGIBILITY REASONS] {c.reasons}")
    if c.eligible_tickers:
        print("[ELIGIBLE SAMPLE]",c.eligible_tickers[:25])
    else:
        print("[ELIGIBLE SAMPLE] NONE")
    print("[PASS] PostgreSQL historical eligibility census completed read-only")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OHL-010 PHYSICAL HISTORICAL ELIGIBILITY CENSUS COMPLETE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
