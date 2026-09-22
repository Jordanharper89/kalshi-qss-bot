\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_321_solana_economic_event_extraction import *
class T(unittest.TestCase):
 def test_flow(self):
  e=SimpleNamespace(signature="s",slot=9,pre_token_balances=({"accountIndex":1,"mint":"M","owner":"W","uiTokenAmount":{"uiAmountString":"1"}},),post_token_balances=({"accountIndex":1,"mint":"M","owner":"W","uiTokenAmount":{"uiAmountString":"3"}},))
  c=SimpleNamespace(signature="s",parsed_type="transferChecked",program_class="SPL_TOKEN",program_id="T",instruction_index=0)
  x=extract_economic_events((e,),(c,))
  print("[EVENTS]",tuple((z.event_type,z.amount_delta) for z in x))
  self.assertTrue(any(z.event_type=="TOKEN_TRANSFER" for z in x)); self.assertTrue(any(z.amount_delta==2 for z in x))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-321 Solana economic-event extraction certified")

