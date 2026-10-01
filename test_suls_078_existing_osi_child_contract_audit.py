import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_078_existing_osi_child_contract_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",{k:v for k,v in d.items() if k!="hits"})
  for h in d.get("hits",[])[:120]:print("[HIT]",h["line"],h["text"])
  if not d.get("exists"):self.fail("EXISTING_OSI_SOLANA_CHILD_NOT_FOUND")
  print("[PASS] SULS-078 existing OSI child contract audit")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
