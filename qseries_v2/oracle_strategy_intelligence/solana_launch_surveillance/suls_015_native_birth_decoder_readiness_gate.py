from __future__ import annotations
import json
from pathlib import Path
def gate(root):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 a=json.loads((base/"native_pool_birth_activation.json").read_text(encoding="utf-8"))
 b=json.loads((base/"native_block_shape_probe.json").read_text(encoding="utf-8"))
 c=json.loads((base/"native_transaction_envelope_probe.json").read_text(encoding="utf-8"))
 d=json.loads((base/"program_registry_exact_readback.json").read_text(encoding="utf-8"))
 ready=bool(a.get("callable_count",0)>0 and b.get("ok") and d.get("address_count",0)>0)
 return {"revision":"SULS_015","native_acquisition_callable":a.get("callable_count",0)>0,
  "native_block_probe_ok":b.get("ok"),"transaction_envelope_contract_present":bool(c.get("signature")),
  "program_identity_evidence_present":d.get("address_count",0)>0,
  "physical_native_birth_decoder_ready":ready,
  "next_required_boundary":"SULS_016_NATIVE_POOL_BIRTH_EVENT_DECODER" if ready else "SULS_016_NATIVE_FOUNDATION_REPAIR",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_decoder_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
