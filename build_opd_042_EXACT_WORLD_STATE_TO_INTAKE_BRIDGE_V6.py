from pathlib import Path
import py_compile
R=Path.cwd(); M=R/"qseries_v2/oracle_predictive_discovery/opd_042_live_state_to_prospective_intake_bridge.py"; T=R/"test_opd_042_live_state_to_prospective_intake_bridge_V6.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens
from qseries_v2.oracle_predictive_data.opd_032_prospective_state_intake_ledger import observe
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
REQ=("anchor_id","ticker","observed_epoch","horizon_seconds","anchor_price","kalshi_state","coinbase_hf_state","crypto_condition_state","learned_state")
FORBIDDEN={"future_target","future_return","mfe","mae","resolution_epoch"}
def snapshot_from_world_state(state_at_t,root=None):
 if not isinstance(state_at_t,dict): raise TypeError("state_at_t must be dict")
 if FORBIDDEN.intersection(state_at_t): raise ValueError("POST_T_OR_OUTCOME_FIELD_REJECTED")
 if any(k not in state_at_t for k in REQ): raise ValueError("MISSING_EXACT_WORLD_STATE_FIELD")
 root=Path(root or Path.cwd()); tokens=materialize_exact_live_tokens(root,state_at_t)
 return {"anchor_id":state_at_t["anchor_id"],"ticker":state_at_t["ticker"],"observed_epoch":float(state_at_t["observed_epoch"]),"horizon_seconds":int(state_at_t["horizon_seconds"]),"anchor_price":state_at_t["anchor_price"],"tokens":list(tokens)}
def intake_world_state(state_at_t,root=None):
 root=Path(root or Path.cwd()); return observe(snapshot_from_world_state(state_at_t,root),root)
""",encoding="utf-8")
T.write_text("""import json,tempfile,time,shutil
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge import snapshot_from_world_state,intake_world_state
r=Path(tempfile.mkdtemp()); rt=r/"runtime/predictive_data";rt.mkdir(parents=True)
src=Path.cwd()/"runtime/predictive_data/opd_031_prospective_candidate_freeze.json";shutil.copy2(src,rt/src.name)
f=json.loads(src.read_text()); now=max(time.time(),float(f["activation_epoch"])+1)
x={"anchor_id":"V6","ticker":"KXBTC-V6","observed_epoch":now,"horizon_seconds":5,"anchor_price":.54,"kalshi_state":{"spread":2,"volume":100},"coinbase_hf_state":{"5s":{"return":.001,"max_event_gap_seconds":.5}},"crypto_condition_state":{"fastest_fee_rate":{"direction":"LOW","value":2}},"learned_state":{"timing_certified":True,"return_fraction":.001,"condition_vector":["['bitcoin', 'fastest_fee_rate', 2.0, 'LOW']"]}}
s=snapshot_from_world_state(x,Path.cwd()); assert "future_target" not in s and s["tokens"]; row=intake_world_state(x,r);assert row["post_freeze"] is True
print("[TOKENS]",len(s["tokens"]));print("[PASS] OPD-042 exact world-state -> OPD-032 intake contract certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-042 V6 installed")
