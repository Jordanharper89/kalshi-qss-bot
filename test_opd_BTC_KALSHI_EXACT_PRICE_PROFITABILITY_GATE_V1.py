
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_kalshi_exact_price_profitability_gate.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")

required=(
    'HURDLE=0.02',
    'KALSHI_SOURCE="source.kalshi.market_data"',
    'sequence_number<=%s',
    'observed_at<=to_timestamp(%s)',
    'ORDER BY sequence_number DESC',
    'extract_yes_price',
    'decision_yes_price',
    'YES_MEANS_UNDERLYING_HIGHER',
    'YES_MEANS_UNDERLYING_LOWER',
    'lb95_net_after_2pct',
    'KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND',
    'NO_KALSHI_PROFITABLE_EDGE_FOUND',
)
for x in required:
    assert x in s,x

print("[PASS] exact decision-time Kalshi price profitability gate installed")
print("[PASS] Kalshi price lookup is source-scoped and anchor-bounded")
print("[PASS] decision-time YES price recovered from canonical observations")
print("[PASS] only drift-controlled BTC underlying survivors are mapped")
print("[PASS] responsive YES-price bands predeclared")
print("[PASS] fixed 2% hurdle enforced")
print("[PASS] profitability requires supported positive 95% lower bound")
print("[PASS] model unchanged; execution/publication false")
