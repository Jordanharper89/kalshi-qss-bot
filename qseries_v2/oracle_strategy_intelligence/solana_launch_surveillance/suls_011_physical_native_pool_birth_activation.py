from __future__ import annotations
import json,inspect
from pathlib import Path

CANDIDATES=(
 ("qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition","acquire_solana_mainnet_chain_state"),
 ("qseries_v2.oracle_adapters.independent.oad_149_solana_finalized_block_activity_acquisition","acquire_solana_finalized_block_activity"),
 ("qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream","acquire_finalized_block_batch"),
)

def activate():
 rows=[]
 for modname,fnname in CANDIDATES:
  try:
   mod=__import__(modname,fromlist=[fnname]);fn=getattr(mod,fnname)
   sig=str(inspect.signature(fn))
   rows.append({"module":modname,"function":fnname,"signature":sig,"callable":True})
  except Exception as e:
   rows.append({"module":modname,"function":fnname,"callable":False,"error":f"{type(e).__name__}: {e}"})
 usable=[r for r in rows if r.get("callable")]
 return {"revision":"SULS_011","native_candidates":rows,"callable_count":len(usable),
  "physical_native_activation_candidate":usable[0] if usable else None,
  "execution_authority":False,"read_only":True}

def write(root):
 d=activate()
 p=root/"runtime_state/solana_opportunities/launch_surveillance/native_pool_birth_activation.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
