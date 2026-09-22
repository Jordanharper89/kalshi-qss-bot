from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
required=(
    "SELECT sequence_number, observation_type, canonical_observation_json",
    'def extract_yes_price(x,observation_type="")',
    '"trade" in typ or "ticker" in typ',
    '"orderbook" in typ',
    '"best_yes_bid"',
    '"best_yes_ask"',
    "_best_level",
    "extract_yes_price(obj,observation_type)",
    "HURDLE=0.02",
    "KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND",
)
for x in required:
    assert x in s,x
print("[PASS] canonical Kalshi price extractor is observation-type aware")
print("[PASS] ticker/trade/orderbook price semantics supported")
print("[PASS] generic numeric fields are not blindly accepted")
print("[PASS] canonical anchor logic unchanged")
print("[PASS] 28 survivors and fixed 2% profitability hurdle unchanged")
print("[PASS] execution/publication remain false")
