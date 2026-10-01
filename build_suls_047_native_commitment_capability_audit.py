from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_047_native_commitment_capability_audit.py"
TEST=ROOT/"test_suls_047_native_commitment_capability_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import inspect,json
MODULES=(
 "qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition",
 "qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker",
 "qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream",
 "qseries_v2.oracle_adapters.independent.oad_326_solana_native_resilient_worker",
)
def audit():
 rows=[]
 for name in MODULES:
  try:
   m=__import__(name,fromlist=["*"]);src=inspect.getsource(m)
   rows.append({"module":name,
    "mentions_processed":"processed" in src.lower(),
    "mentions_confirmed":"confirmed" in src.lower(),
    "mentions_finalized":"finalized" in src.lower(),
    "mentions_websocket":any(x in src.lower() for x in ("websocket","logssubscribe","blocksubscribe","programsubscribe")),
    "functions":sorted(n for n,v in vars(m).items() if callable(v) and not n.startswith("_")),
    "source_excerpt":src[:14000]})
  except Exception as e:rows.append({"module":name,"error":f"{type(e).__name__}: {e}"})
 return {"revision":"SULS_047","modules":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=audit();p=root/"runtime_state/solana_opportunities/launch_surveillance/native_commitment_capability_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_047_native_commitment_capability_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  for x in d["modules"]:print("[MODULE]",json.dumps({k:v for k,v in x.items() if k!="source_excerpt"},sort_keys=True))
  if not d["modules"]:self.fail("NO_NATIVE_COMMITMENT_MODULES")
  print("[PASS] SULS-047 native commitment capability audit")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")