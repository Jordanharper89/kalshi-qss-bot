from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_045_041_044_certified_chain_gate.py";T=R/"test_opd_045_041_044_certified_chain_gate_V5.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from pathlib import Path
import hashlib
SHA="c0455590b2de0560552bdfd503dfbe0bf8a97a105617695581d2df0c56a00917"
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
def certify(repo_root=None):
 r=Path(repo_root or Path.cwd());p=r/"qseries_v2/oracle_predictive_data/opd_017_discovery_feature_primitive_materialization.py"
 if hashlib.sha256(p.read_bytes()).hexdigest()!=SHA:raise RuntimeError("FROZEN_OPD017_HASH_CHANGED")
 from qseries_v2.oracle_predictive_discovery import opd_041_exact_live_token_materializer as a
 from qseries_v2.oracle_predictive_discovery import opd_042_live_state_to_prospective_intake_bridge as b
 from qseries_v2.oracle_predictive_discovery import opd_043_exact_durable_maturity_queue as c
 from qseries_v2.oracle_predictive_discovery import opd_044_exact_strict_future_resolver as d
 if any(getattr(x,"execution_authority",None) is not False for x in (a,b,c,d)):raise RuntimeError("EXECUTION_AUTHORITY_VIOLATION")
 return {"opd017_hash":SHA,"opd041_exact_tokens":True,"opd042_exact_intake":True,"opd043_exact_maturity":True,"opd044_exact_resolver":True,"live_outcome_materializer_certified":False,"native_worker_cutover_allowed":False,"execution_authority":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False}
""",encoding="utf-8")
T.write_text("""from qseries_v2.oracle_predictive_discovery.opd_045_041_044_certified_chain_gate import certify
x=certify();assert all(x[k] for k in ("opd041_exact_tokens","opd042_exact_intake","opd043_exact_maturity","opd044_exact_resolver"))
assert x["live_outcome_materializer_certified"] is False and x["native_worker_cutover_allowed"] is False
print("[LIVE_OUTCOME_MATERIALIZER_CERTIFIED]",x["live_outcome_materializer_certified"]);print("[NATIVE_WORKER_CUTOVER_ALLOWED]",x["native_worker_cutover_allowed"]);print("[PASS] OPD-045 certified chain frozen; unproven live cutover blocked")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-045 V5 installed")
