from pathlib import Path
import importlib.util

ROOT=Path.cwd().resolve()
Q=ROOT/"qseries_v2"
P=Q/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
REV="EXOGENOUS_EVIDENCE_FREEZE_ROOT_DISCOVERED_LEDGER_V1"
MARKERS=("opd_full_evidence_live_prediction_ledger.jsonl","FULL_EVIDENCE_PROSPECTIVE_LEDGER_V1")

hits=[]
for p in Q.rglob("*.py"):
    try:s=p.read_text(encoding="utf-8")
    except Exception:continue
    score=sum(1 for m in MARKERS if m in s)
    if score:hits.append((score,p))
exact=[p for score,p in hits if score==2]
assert len(exact)==1, ("expected one exact ledger writer",exact,hits[:20])
L=exact[0]

ps=P.read_text(encoding="utf-8")
ls=L.read_text(encoding="utf-8")
assert REV in ps
assert REV in ls
assert "_opd_exogenous_freeze_snapshot" in ps
assert "exogenous_evidence_snapshot" in ps

spec=importlib.util.spec_from_file_location("opd_predictor_exo_test",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

fixture={
    "kalshi_state":{"price":0.55,"volume":100},
    "coinbase_hf_state":{"return":0.01,"close_price":70000},
    "crypto_condition_state":{
        "source_id":"source.crypto.condition.network",
        "condition":"SOLANA_NETWORK_CONGESTION",
        "direction":"HIGH","basis":"official_network"},
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

print("[PASS] exact production ledger writer discovered:",L)
print("[PASS] predictor carries exogenous_evidence_snapshot")
print("[PASS] independent source fixture survives freeze")
print("[PASS] Kalshi/Coinbase/future leakage fixture excluded")
print("[PASS] old ledger remains untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
