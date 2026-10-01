from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_014_program_registry_exact_readback.py"
TEST=ROOT/"test_suls_014_program_registry_exact_readback.py"

MOD_TEXT=r"""from __future__ import annotations
import inspect,json,re
from pathlib import Path
from qseries_v2.oracle_adapters.independent import oad_333_solana_authoritative_program_identity_registry as reg
from qseries_v2.oracle_adapters.independent import oad_353_solana_final_verified_economic_program_expansion as exp

B58=re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")
def readback():
 src1=inspect.getsource(reg);src2=inspect.getsource(exp)
 addrs=sorted(set(B58.findall(src1+"\n"+src2)))
 labels={}
 for a in addrs:
  ctx=(src1+"\n"+src2)
  i=ctx.find(a);window=ctx[max(0,i-220):i+220].lower()
  fam=[]
  for k in ("pump","meteora","raydium","orca","jupiter","token2022","memo"):
   if k in window:fam.append(k)
  labels[a]=fam
 return {"revision":"SULS_014","address_count":len(addrs),"addresses":addrs,
  "context_labels":labels,"execution_authority":False,"read_only":True}
def write(root):
 d=readback();p=root/"runtime_state/solana_opportunities/launch_surveillance/program_registry_exact_readback.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_014_program_registry_exact_readback import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_readback(self):
  p,d=write(ROOT);print("[ADDRESS_COUNT]",d["address_count"])
  for a in d["addresses"]:print("[PROGRAM_ID]",a,json.dumps(d["context_labels"].get(a,[])))
  if d["address_count"]==0:self.fail("NO_PROGRAM_IDS_FOUND")
  print("[PASS] SULS-014 exact program-registry readback")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-014 PROGRAM REGISTRY EXACT READBACK");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
