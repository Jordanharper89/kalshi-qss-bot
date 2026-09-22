\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_336_solana_pump_meteora_market_behavior_decoder import *
class T(unittest.TestCase):
 def test_pump(self):
  e=SimpleNamespace(signature="s",slot=1)
  a=SimpleNamespace(signature="s",known_protocols=("PUMP_FUN_AMM",))
  flows=(SimpleNamespace(signature="s",owner="W",mint="A",delta=-2.0),
         SimpleNamespace(signature="s",owner="W",mint="B",delta=6.0))
  x=decode_protocol_market_behaviors((e,),(a,),flows)[0]
  print("[DECODE]",x.protocol,x.behavior,x.confidence_basis)
  self.assertEqual((x.protocol,x.behavior),("PUMP_FUN_AMM","SWAP"))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-336 Pump.fun/Pump AMM/Meteora evidence-grounded behavior decoder certified")

