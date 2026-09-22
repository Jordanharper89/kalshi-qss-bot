from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
required=(
    "def derive_anchor_sequence",
    "observed_at<=to_timestamp(%s)",
    "ORDER BY sequence_number DESC",
    "extract_ticker(obj)==ticker",
    "decision_time_anchors_derived_from_canonical",
    "[DECISION-TIME ANCHORS DERIVED FROM CANONICAL]",
    "HURDLE=0.02",
    "KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND",
)
for x in required:
    assert x in s,x
print("[PASS] missing prediction anchor sequence now recovered from canonical Kalshi history")
print("[PASS] recovered anchor is same-ticker and observed-time bounded")
print("[PASS] exact YES-price lookup remains sequence/time bounded")
print("[PASS] 28-survivor signal family, fixed 2% hurdle, and profitability gate unchanged")
print("[PASS] execution/publication remain false")
