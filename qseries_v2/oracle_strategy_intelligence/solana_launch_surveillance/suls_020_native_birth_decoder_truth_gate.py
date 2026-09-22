from __future__ import annotations
import json
from pathlib import Path
def gate(root):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 r=json.loads((base/"native_birth_candidate_physical_gate.json").read_text(encoding="utf-8"))
 observed=bool(r.get("physical_candidate_observed"))
 return {"revision":"SULS_020","native_candidate_observed":observed,
  "candidate_count":r.get("candidate_count",0),"transactions_examined":r.get("transactions_examined",0),
  "verified_pool_birth_decoder_ready":False,
  "next_required_boundary":"SULS_021_EXACT_PROGRAM_INSTRUCTION_POOL_BIRTH_VERIFICATION" if observed else "SULS_021_NATIVE_BIRTH_CAPTURE_WINDOW_EXPANSION",
  "execution_authority":False,"read_only":True,
  "scope":"Candidate observation is not yet exact instruction-level pool-birth verification"}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_decoder_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
