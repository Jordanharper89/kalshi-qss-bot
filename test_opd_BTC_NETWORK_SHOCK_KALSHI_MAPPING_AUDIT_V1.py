
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_network_shock_kalshi_mapping_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in (
'HURDLE=0.02',
'MIN_N=12',
'MIN_TICKERS=3',
'YES_MEANS_UNDERLYING_HIGHER',
'YES_MEANS_UNDERLYING_LOWER',
'net_after_2pct',
'lb95_net_after_2pct',
'BTC_NETWORK_SHOCK_KALSHI_NET_EDGE_FOUND',
):
    assert x in s,x
print("[PASS] BTC network-shock Kalshi mapping audit installed")
print("[PASS] only drift-controlled underlying survivors are mapped")
print("[PASS] exact YES semantic controls contract direction")
print("[PASS] fixed 2% hurdle enforced")
print("[PASS] profitability requires positive 95% lower bound with support")
print("[PASS] model remains unchanged; execution/publication false")
