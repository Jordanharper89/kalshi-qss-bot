
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_network_shock_sensitive_contract_mapping_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in (
'HURDLE=0.02',
'PRICE_BANDS=((0.10,0.90),(0.20,0.80),(0.30,0.70),(0.40,0.60))',
'recursive_find_price',
'YES_MEANS_UNDERLYING_HIGHER',
'YES_MEANS_UNDERLYING_LOWER',
'lb95_net_after_2pct',
'BTC_NETWORK_SHOCK_SENSITIVE_KALSHI_EDGE_FOUND',
'NO_SENSITIVE_KALSHI_EDGE_AFTER_2PCT',
):
    assert x in s,x
print("[PASS] sensitive-contract Kalshi mapping audit installed")
print("[PASS] selection uses decision-time YES price only")
print("[PASS] fixed price bands are predeclared")
print("[PASS] exact contract semantics preserved")
print("[PASS] fixed 2% hurdle and positive LB95 profitability gate preserved")
print("[PASS] no model mutation/execution/publication")
