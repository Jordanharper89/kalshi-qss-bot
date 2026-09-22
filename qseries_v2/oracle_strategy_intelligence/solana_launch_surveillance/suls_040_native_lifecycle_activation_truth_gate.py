from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 r=json.loads((b/"native_vault_balance_readback.json").read_text(encoding="utf-8"))
 n=json.loads((b/"native_lifecycle_snapshots.json").read_text(encoding="utf-8"))
 s=json.loads((b/"prospective_lifecycle_schedule.json").read_text(encoding="utf-8"))
 f=json.loads((b/"fresh_birth_lifecycle_admission.json").read_text(encoding="utf-8"))
 physical=bool(r.get("snapshot_count",0)>0 and n.get("snapshot_count",0)>0)
 schedule=bool(s.get("pending_count",0)>0)
 return {"revision":"SULS_040","physical_native_vault_readback":physical,
  "prospective_schedule_ready":schedule,"fresh_births_currently_admitted":int(f.get("fresh_birth_count",0)),
  "continuous_native_lifecycle_active":False,"profitable_edge_claimed":False,
  "next_required_boundary":"SULS_041_CONTINUOUS_NATIVE_BIRTH_AND_AGE_1S_5S_15S_WORKER",
  "execution_authority":False,"read_only":True,
  "scope":"Infrastructure ready; repeated prospective lifecycle outcomes not yet accumulated"}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_lifecycle_activation_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
