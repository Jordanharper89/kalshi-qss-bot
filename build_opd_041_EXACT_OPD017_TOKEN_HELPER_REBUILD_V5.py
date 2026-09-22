from pathlib import Path
import py_compile
R=Path.cwd()
M=R/"qseries_v2/oracle_predictive_discovery/opd_041_exact_live_token_materializer.py"
T=R/"test_opd_041_exact_live_token_materializer_REPAIR_V5.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from pathlib import Path
import hashlib,importlib.util
SOURCE_PATH=r"qseries_v2\\oracle_predictive_data\\opd_017_discovery_feature_primitive_materialization.py"
SOURCE_SHA256="c0455590b2de0560552bdfd503dfbe0bf8a97a105617695581d2df0c56a00917"
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
def _load(root):
 p=Path(root)/SOURCE_PATH
 if hashlib.sha256(p.read_bytes()).hexdigest()!=SOURCE_SHA256: raise RuntimeError("OPD-017 frozen source hash changed")
 s=importlib.util.spec_from_file_location("_opd017_frozen",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 if not callable(getattr(m,"_tokens",None)): raise RuntimeError("OPD-017 frozen _tokens helper disappeared")
 return m._tokens
def materialize_exact_live_tokens(root,state_at_t):
 if not isinstance(state_at_t,dict): raise TypeError("state_at_t must be dict")
 return tuple(_load(root)(state_at_t))
""",encoding="utf-8")
T.write_text("""from pathlib import Path
import importlib.util
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens
r=Path.cwd();p=r/"qseries_v2/oracle_predictive_data/opd_017_discovery_feature_primitive_materialization.py"
s=importlib.util.spec_from_file_location("_frozen",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x={"horizon_seconds":5,"anchor_price":.54,"kalshi_state":{"spread":2,"volume":100},"coinbase_hf_state":{"5s":{"return":.001,"max_event_gap_seconds":.5}},"crypto_condition_state":{"fastest_fee_rate":{"direction":"LOW","value":2}},"learned_state":{"timing_certified":True,"return_fraction":.001,"condition_vector":["['bitcoin', 'fastest_fee_rate', 2.0, 'LOW']"]}}
a=tuple(m._tokens(x));b=materialize_exact_live_tokens(r,x)
assert a==b,(a,b)
assert "L:COND:['bitcoin', 'fastest_fee_rate', 2.0, 'LOW']" in b
print("[TOKENS]",b);print("[PASS] OPD-041 exact frozen OPD-017 _tokens semantics certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True)
print("[PASS] OPD-041 V5 exact-helper rebuild installed")
