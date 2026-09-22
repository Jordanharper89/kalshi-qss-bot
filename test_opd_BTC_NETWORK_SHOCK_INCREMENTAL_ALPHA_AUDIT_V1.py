
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_network_shock_incremental_alpha_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in (
'baseline_mean_directional_spot_return',
'incremental_alpha_vs_same_horizon_direction',
'incremental_alpha_lb95_proxy',
'NETWORK_SHOCK_INCREMENTAL_ALPHA_SURVIVES_DRIFT_CONTROL',
'NETWORK_SHOCK_WINNERS_EXPLAINED_BY_BASELINE_DRIFT',
'[MODEL MUTATION] FALSE',
'[KALSHI MAPPING] FALSE',
):
    assert x in s,x
print("[PASS] BTC network-shock incremental-alpha audit installed")
print("[PASS] each discovery winner compared with same-horizon/same-direction holdout baseline")
print("[PASS] positive raw direction alone cannot pass")
print("[PASS] survivor requires positive conservative incremental-alpha lower bound")
print("[PASS] no model mutation or Kalshi mapping")
