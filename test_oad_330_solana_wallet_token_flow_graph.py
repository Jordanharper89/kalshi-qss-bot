\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_330_solana_wallet_token_flow_graph import *
class T(unittest.TestCase):
 def test_flows(self):
  e=SimpleNamespace(signature="s",slot=1,pre_token_balances=({"accountIndex":1,"mint":"SOLX","owner":"W","uiTokenAmount":{"uiAmountString":"10"}},{"accountIndex":2,"mint":"USDC","owner":"W","uiTokenAmount":{"uiAmountString":"2"}},),post_token_balances=({"accountIndex":1,"mint":"SOLX","owner":"W","uiTokenAmount":{"uiAmountString":"7"}},{"accountIndex":2,"mint":"USDC","owner":"W","uiTokenAmount":{"uiAmountString":"5"}},))
  x=build_wallet_token_flows((e,))
  print("[FLOWS]",tuple((z.owner,z.mint,z.delta) for z in x))
  self.assertEqual(len(x),2);self.assertEqual({z.delta for z in x},{-3.0,3.0})
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-330 wallet/token balance-flow graph certified")

