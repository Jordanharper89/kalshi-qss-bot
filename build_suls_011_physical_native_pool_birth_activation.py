from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_011_physical_native_pool_birth_activation.py"
TEST=ROOT/"test_suls_011_physical_native_pool_birth_activation.py"

MOD_TEXT=r"""from __future__ import annotations
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
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_011_physical_native_pool_birth_activation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_activation(self):
  p,d=write(ROOT)
  print("[CALLABLE_COUNT]",d["callable_count"])
  for r in d["native_candidates"]:print("[NATIVE_CANDIDATE]",json.dumps(r,sort_keys=True))
  print("[PHYSICAL_NATIVE_ACTIVATION_CANDIDATE]",json.dumps(d["physical_native_activation_candidate"],sort_keys=True))
  if d["callable_count"]==0:self.fail("NO_CALLABLE_NATIVE_SOLANA_ACQUISITION")
  print("[PASS] SULS-011 physical native pool-birth activation candidate")
  print("[SCOPE] Callable activation candidate only; pool-birth decode not yet claimed")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-011 PHYSICAL NATIVE POOL-BIRTH ACTIVATION");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
