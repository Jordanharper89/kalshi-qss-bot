import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_072_existing_oracle_launcher_contract_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);print("[LAUNCHER_COUNT]",d["launcher_count"])
  for x in d["launchers"]:
   print("[LAUNCHER]",x["path"],"lines=",x["line_count"],"suls_import=",x["imports_solana_launch_surveillance"])
   for h in x["hits"][:80]:print("[HIT]",h["line"],h["text"])
  if d["launcher_count"]==0:self.fail("NO_EXISTING_ORACLE_LAUNCHER_FOUND")
  print("[PASS] SULS-072 existing Oracle launcher contract audit")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
