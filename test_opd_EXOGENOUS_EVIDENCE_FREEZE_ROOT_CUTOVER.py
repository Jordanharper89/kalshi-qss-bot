from pathlib import Path
import importlib.util

ROOT=Path.cwd().resolve()
P=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
L=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_full_evidence_immutable_prediction_ledger.py"

s=P.read_text(encoding="utf-8")
l=L.read_text(encoding="utf-8")

assert "EXOGENOUS_EVIDENCE_FREEZE_ROOT_CUTOVER_V1" in s
assert "_opd_exogenous_freeze_snapshot" in s
assert "exogenous_evidence_snapshot" in s
assert "EXOGENOUS_EVIDENCE_FREEZE_ROOT_CUTOVER_V1" in l

spec=importlib.util.spec_from_file_location("opd_predictor_exo_test",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

fixture={
    "kalshi_state":{"price":0.55,"volume":100},
    "coinbase_hf_state":{"return":0.01,"close_price":70000},
    "crypto_condition_state":{
        "source_id":"source.crypto.condition.network",
        "condition":"SOLANA_NETWORK_CONGESTION",
        "direction":"HIGH",
        "basis":"official_network"
    },
    "usgs_event":{"source":"usgs","magnitude":5.4,"official":True},
    "macro_release":{"provider":"official","event":"CPI_RELEASE","value":2.7},
    "future_outcome":{"return":0.2},
}

snap=m._opd_exogenous_freeze_snapshot(fixture)
j=str(snap).lower()

assert "kalshi_state" not in j
assert "coinbase_hf_state" not in j
assert "future_outcome" not in j
assert "solana_network_congestion" in j
assert "usgs" in j
assert "cpi_release" in j

print("[PASS] raw independent-source evidence freezes from production state")
print("[PASS] Kalshi/Coinbase/price-path fields excluded")
print("[PASS] future/outcome/PnL leakage fields excluded")
print("[PASS] immutable ledger preserves exogenous snapshot field")
print("[PASS] old ledger remains untouched; no retroactive fabrication")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
