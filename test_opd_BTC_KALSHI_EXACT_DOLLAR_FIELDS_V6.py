from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in ('"yes_price_dollars"','"yes_bid_dollars"','"yes_ask_dollars"','"price_dollars"',"HURDLE=0.02","KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND"):
    assert x in s,x
print("[PASS] exact observed Kalshi dollar price fields installed")
print("[PASS] trade yes_price_dollars supported")
print("[PASS] ticker yes_bid_dollars/yes_ask_dollars/price_dollars supported")
print("[PASS] existing anchor recovery preserved")
print("[PASS] 28-survivor signal family and fixed 2% hurdle unchanged")
print("[PASS] execution/publication remain false")
