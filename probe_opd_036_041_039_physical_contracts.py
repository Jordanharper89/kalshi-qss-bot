from pathlib import Path
import inspect

root=Path.cwd()

from qseries_v2.oracle_predictive_data.opd_036_live_production_boundary_contract import build
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens
from qseries_v2.oracle_predictive_data.opd_039_durable_horizon_maturity_queue import rebuild,mature

print("="*100)
print("[OPD-036 SIGNATURE]",inspect.signature(build))
x=build(root)
print("[OPD-036 RETURN TYPE]",type(x).__module__+"."+type(x).__qualname__)
print("[OPD-036 RETURN REPR]",repr(x)[:12000])

print("="*100)
print("[OPD-041 SIGNATURE]",inspect.signature(materialize_exact_live_tokens))

print("="*100)
print("[OPD-039 REBUILD SIGNATURE]",inspect.signature(rebuild))
print("[OPD-039 MATURE SIGNATURE]",inspect.signature(mature))
r=rebuild(root)
m=mature(root)
print("[OPD-039 REBUILD TYPE]",type(r).__module__+"."+type(r).__qualname__)
print("[OPD-039 REBUILD REPR]",repr(r)[:6000])
print("[OPD-039 MATURE TYPE]",type(m).__module__+"."+type(m).__qualname__)
print("[OPD-039 MATURE REPR]",repr(m)[:6000])

print("="*100)
print("[PASS] physical contracts inspected read-only; no production files changed")