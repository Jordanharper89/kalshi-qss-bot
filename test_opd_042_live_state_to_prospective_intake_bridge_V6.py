import json,tempfile,time,shutil
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge import snapshot_from_world_state,intake_world_state
r=Path(tempfile.mkdtemp()); rt=r/"runtime/predictive_data";rt.mkdir(parents=True)
src=Path.cwd()/"runtime/predictive_data/opd_031_prospective_candidate_freeze.json";shutil.copy2(src,rt/src.name)
f=json.loads(src.read_text()); now=max(time.time(),float(f["activation_epoch"])+1)
x={"anchor_id":"V6","ticker":"KXBTC-V6","observed_epoch":now,"horizon_seconds":5,"anchor_price":.54,"kalshi_state":{"spread":2,"volume":100},"coinbase_hf_state":{"5s":{"return":.001,"max_event_gap_seconds":.5}},"crypto_condition_state":{"fastest_fee_rate":{"direction":"LOW","value":2}},"learned_state":{"timing_certified":True,"return_fraction":.001,"condition_vector":["['bitcoin', 'fastest_fee_rate', 2.0, 'LOW']"]}}
s=snapshot_from_world_state(x,Path.cwd()); assert "future_target" not in s and s["tokens"]; row=intake_world_state(x,r);assert row["post_freeze"] is True
print("[TOKENS]",len(s["tokens"]));print("[PASS] OPD-042 exact world-state -> OPD-032 intake contract certified")
