from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor import latest_live_anchor,_opd_load_exogenous_canonical_asof
root=Path.cwd().resolve()
a=latest_live_anchor(root)
if not a: raise SystemExit("[FAIL] no live anchor")
x=_opd_load_exogenous_canonical_asof(a,root)
print("[ANCHOR]",a.get("ticker"),a.get("anchor_sequence_boundary"),a.get("observed_epoch"))
print("[EXOGENOUS SOURCES]",len(x))
for k,v in list(x.items())[:64]:
    print("[SOURCE]",v.get("sequence_number"),v.get("source_id"),v.get("observation_type"))
if not x: raise SystemExit("[FAIL] no eligible independent canonical evidence at live anchor")
print("[PASS] independent canonical evidence physically reachable at exact live anchor")
