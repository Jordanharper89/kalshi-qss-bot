from pathlib import Path
import json

R=Path.cwd()
P=R/"qseries_v2"/"oracle_predictive_discovery"
D=R/"runtime"/"predictive_data"
P.mkdir(parents=True,exist_ok=True); D.mkdir(parents=True,exist_ok=True)

req=[
 P/"opd_041_exact_live_token_materializer.py",
 R/"qseries_v2"/"oracle_predictive_data"/"opd_032_prospective_state_intake_ledger.py",
 R/"qseries_v2"/"oracle_predictive_data"/"opd_036_live_production_boundary_contract.py",
]
for p in req:
    if not p.is_file(): raise RuntimeError("missing certified dependency: "+str(p))

mod=P/"opd_042_live_state_to_prospective_intake_bridge.py"
mod.write_text(r'''from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens
from qseries_v2.oracle_predictive_data.opd_032_prospective_state_intake_ledger import observe
from qseries_v2.oracle_predictive_data.opd_036_live_production_boundary_contract import build as production_boundary

execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def bridge_snapshot(snapshot, root=None):
    root=Path(root or Path.cwd()).resolve()
    if not isinstance(snapshot,dict):
        raise TypeError("OPD-042 requires state-at-T snapshot dict")
    tokens=materialize_exact_live_tokens(root,snapshot)
    enriched=dict(snapshot)
    enriched["feature_tokens"]=list(tokens)
    return observe(enriched,root)

def production_snapshot(root=None):
    root=Path(root or Path.cwd()).resolve()
    snap=production_boundary(root)
    if not isinstance(snap,dict):
        raise TypeError("OPD-036 build(root) did not return dict state-at-T boundary")
    return snap

def cycle(root=None):
    root=Path(root or Path.cwd()).resolve()
    return bridge_snapshot(production_snapshot(root),root)
''',encoding="utf-8")

test=R/"test_opd_042_live_state_to_prospective_intake_bridge.py"
test.write_text(r'''import inspect
from pathlib import Path
from qseries_v2.oracle_predictive_discovery import opd_042_live_state_to_prospective_intake_bridge as m
from qseries_v2.oracle_predictive_data import opd_032_prospective_state_intake_ledger as i
from qseries_v2.oracle_predictive_data import opd_036_live_production_boundary_contract as b
assert tuple(inspect.signature(i.observe).parameters)==("snapshot","root")
assert tuple(inspect.signature(b.build).parameters)==("root",)
assert m.execution_authority is False and m.probability_enabled is False
assert m.direction_enabled is False and m.publication_allowed is False
assert callable(m.bridge_snapshot) and callable(m.production_snapshot) and callable(m.cycle)
print("[OPD032] observe(snapshot, root=None)")
print("[OPD036] build(root=None)")
print("[PASS] OPD-042 exact named live-state intake bridge certified")
''',encoding="utf-8")

manifest={
 "schema_version":"OPD-042","opd032_callable":"observe(snapshot, root=None)",
 "opd036_callable":"build(root=None)","opd041_exact_token_semantics":True,
 "execution_authority":False,"probability_enabled":False,
 "direction_enabled":False,"publication_allowed":False
}
(D/"opd_042_exact_named_contract.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("[PASS] OPD-042 V3 installer complete")
