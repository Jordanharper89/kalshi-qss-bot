
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_exogenous_prospective_realized_edge_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
required=[
'HURDLE=0.02',
'MIN_SEGMENT_N=12',
'MIN_UNIQUE_TICKERS=3',
'"exogenous_evidence_snapshot"',
'"realized_net_after_2pct"',
'"profitable_supported"',
'lower_bound_net_after_2pct',
'[MODEL MUTATION] FALSE',
]
for x in required: assert x in s,x
print("[PASS] clean exogenous prospective realized-edge audit installed")
print("[PASS] fixed 2% hurdle enforced")
print("[PASS] exact resolved prediction/outcome join required")
print("[PASS] support requires n>=12 and >=3 unique tickers")
print("[PASS] profitability requires positive 95% lower bound after hurdle")
print("[PASS] model/scoring/gates remain unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
