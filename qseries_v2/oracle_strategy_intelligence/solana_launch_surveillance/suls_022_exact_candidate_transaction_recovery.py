from __future__ import annotations
import json
from dataclasses import asdict,is_dataclass
from qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from qseries_v2.oracle_adapters.independent.oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes

def recover(root):
 src=root/"runtime_state/solana_opportunities/launch_surveillance/exact_program_instruction_birth_verification.json"
 d=json.loads(src.read_text(encoding="utf-8"));out=[]
 for t in [x for x in d.get("verified_candidates",[]) if x.get("instruction_level_birth_candidate")]:
  slot=int(t["slot"]);sig=str(t["signature"]);batch=acquire_finalized_block_batch(start_slot=slot,limit=1)
  hit=None
  for e in canonical_transaction_envelopes(batch):
   if str(getattr(e,"signature",""))==sig:
    hit=asdict(e) if is_dataclass(e) else {n:getattr(e,n) for n in dir(e) if not n.startswith("_") and not callable(getattr(e,n))}
    break
  out.append({"slot":slot,"signature":sig,"recovered":hit is not None,
   "envelope_fields":[] if hit is None else sorted(hit.keys()),"envelope":hit})
 return {"revision":"SULS_022","target_count":len(out),"recovered_count":sum(x["recovered"] for x in out),
  "transactions":out,"execution_authority":False,"read_only":True}

def write(root):
 d=recover(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_candidate_transaction.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
