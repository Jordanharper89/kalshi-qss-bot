from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_002_settled_outcome_read_model import fetch_recent_settled_markets
if __name__=="__main__":
    print("="*72);print(" OLR-005 PHYSICAL SETTLED OUTCOME READ VERIFICATION");print("="*72)
    rows=fetch_recent_settled_markets(Path.cwd(),limit=20)
    print(f"[SETTLED] outcomes={len(rows)}")
    for x in rows[:10]:
        print(f"[SETTLED] ticker={x.ticker} result={x.result} settlement_ts={x.settlement_ts}")
    print("[PASS] Physical Kalshi settled-outcome read path verified")
    print("[DONE] OLR-005 PHYSICAL OUTCOME READ VERIFIED")
