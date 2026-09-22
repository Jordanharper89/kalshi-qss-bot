\

import unittest
from qseries_v2.oracle_adapters.independent.oad_339_solana_reconciled_program_identity_registry import *
class T(unittest.TestCase):
 def test_reconcile(self):
  a=identify_reconciled_program("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
  b=identify_reconciled_program("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
  c=identify_reconciled_program("NOPE")
  print("[RECONCILED]",a.name,a.source,b.name,b.source,c.name)
  self.assertEqual(a.name,"TOKEN_2022");self.assertEqual(b.name,"PUMP_FUN_AMM");self.assertFalse(c.known)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-339 reconciled Solana program identity registry certified")

