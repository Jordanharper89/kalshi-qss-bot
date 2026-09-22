import json,tempfile,time,shutil
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge import snapshot_from_world_state,intake_world_state
repo=Path.cwd();state_root=Path(tempfile.mkdtemp());rt=state_root/"runtime/predictive_data";rt.mkdir(parents=True)
freeze=repo/"runtime/predictive_data/opd_031_prospective_candidate_freeze.json";shutil.copy2(freeze,rt/freeze.name)
f=json.loads(freeze.read_text());now=max(time.time(),float(f["activation_epoch"])+1)
x={"anchor_id":"V7","ticker":"KXBTC-V7","observed_epoch":now,"horizon_seconds":5,"anchor_price":.54,"kalshi_state":{"spread":2,"volume":100},"coinbase_hf_state":{"5s":{"return":.001,"max_event_gap_seconds":.5}},"crypto_condition_state":{"fastest_fee_rate":{"direction":"LOW","value":2}},"learned_state":{"timing_certified":True,"return_fraction":.001,"condition_vector":["['bitcoin', 'fastest_fee_rate', 2.0, 'LOW']"]}}
s=snapshot_from_world_state(x,repo);assert s["tokens"]
row=intake_world_state(x,state_root,repo);assert row["post_freeze"] is True
assert (rt/"opd_032_prospective_state_ledger.jsonl").exists()
print("[TOKENS]",len(s["tokens"]));print("[STATE_ROOT]",state_root);print("[PASS] OPD-042 repository-root/state-root separation physically certified")
