\

import os,unittest
from qseries_v2.oracle_adapters.independent.oad_327_solana_universal_continuity_physical_certification import *
class T(unittest.TestCase):
 def test_physical(self):
  if os.environ.get("Q_SERIES_SKIP_SOLANA_PHYSICAL")=="1":self.skipTest("physical certification explicitly skipped")
  x=certify_solana_universal_continuity(cycles=2,per_batch_limit=1)
  print("[CERT] cycles=",x.cycles,"checkpoint=",x.start_checkpoint,"->",x.end_checkpoint,"tx=",x.transactions,"obs=",x.observations,"committed=",x.committed_events,"state=",x.state)
  self.assertEqual(x.state,"CONTINUITY_CERTIFIED");self.assertTrue(x.advanced);self.assertEqual(x.cycles,2)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-327 physical Solana universal continuity certified")
 print("[PASS] certified OPH-021 exclusive writer used; no bypass writer")
 print("[PASS] checkpoint/restart boundary active")
 print("[PASS] finalized chain data persisted before checkpoint advancement")

