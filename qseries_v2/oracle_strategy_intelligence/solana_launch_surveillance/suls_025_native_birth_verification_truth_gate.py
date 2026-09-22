from __future__ import annotations
import json
def gate(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/physical_exact_native_pool_birth_gate.json"
 d=json.loads(p.read_text(encoding="utf-8"));n=int(d.get("verified_birth_count",0))
 return {"revision":"SULS_025","exact_native_birth_verified":n>0,"verified_birth_count":n,
  "pool_token_account_roles_resolved":False,"canonical_tradeable_birth_event_ready":False,
  "next_required_boundary":"SULS_026_NATIVE_POOL_TOKEN_ACCOUNT_ROLE_RESOLUTION" if n>0 else "SULS_026_NATIVE_BIRTH_VERIFICATION_REPAIR",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_verification_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
