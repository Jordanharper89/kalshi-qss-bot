from pathlib import Path
import importlib.util
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens
r=Path.cwd();p=r/"qseries_v2/oracle_predictive_data/opd_017_discovery_feature_primitive_materialization.py"
s=importlib.util.spec_from_file_location("_frozen",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
x={"horizon_seconds":5,"anchor_price":.54,"kalshi_state":{"spread":2,"volume":100},"coinbase_hf_state":{"5s":{"return":.001,"max_event_gap_seconds":.5}},"crypto_condition_state":{"fastest_fee_rate":{"direction":"LOW","value":2}},"learned_state":{"timing_certified":True,"return_fraction":.001,"condition_vector":["['bitcoin', 'fastest_fee_rate', 2.0, 'LOW']"]}}
a=tuple(m._tokens(x));b=materialize_exact_live_tokens(r,x)
assert a==b,(a,b)
assert "L:COND:['bitcoin', 'fastest_fee_rate', 2.0, 'LOW']" in b
print("[TOKENS]",b);print("[PASS] OPD-041 exact frozen OPD-017 _tokens semantics certified")
