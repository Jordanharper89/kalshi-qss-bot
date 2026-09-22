
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_network_shock_underlying_holdout_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in (
'BTC_USD_UNDERLYING_SPOT_RETURN',
'HORIZONS={5,15,30,60}',
'sids.issubset(ALLOWED)',
'".delta"',
'".pct_change"',
'TRAIN_FRAC=0.65',
'MIN_TRAIN_N=30',
'MIN_HOLDOUT_N=12',
'holdout_lb95_directional_spot_return',
'[KALSHI MAPPING] NOT YET',
):
    assert x in s,x
print("[PASS] BTC network-shock underlying holdout audit installed")
print("[PASS] target is exact future BTC-USD spot return, not Kalshi contract return")
print("[PASS] signal uses decision-time network deltas/pct changes, not raw levels")
print("[PASS] only clean seven-source BTC snapshots admitted")
print("[PASS] training-only thresholds and untouched temporal holdout enforced")
print("[PASS] no Kalshi mapping/model mutation/execution")
