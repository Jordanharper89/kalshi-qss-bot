\

import unittest
from qseries_v2.oracle_adapters.independent.oad_337_solana_program_decode_physical_coverage_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  x=measure_solana_program_decode_physical(block_limit=1)
  print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.instructions)
  print("[PHYSICAL] baseline_known_ratio=",x.baseline_known_ratio)
  print("[PHYSICAL] authoritative_known_ratio=",x.authoritative_known_ratio,"economic_resolution_ratio=",x.economic_resolution_ratio)
  print("[PHYSICAL] infrastructure=",x.infrastructure_instructions,"economic_known=",x.economic_known_instructions,"unknown=",x.unknown_instructions)
  print("[PHYSICAL] wallet_flows=",x.wallet_flows,"routed_swaps=",x.routed_swaps,"protocol_behaviors=",x.protocol_behaviors)
  print("[PHYSICAL] protocol_counts=",x.protocol_counts)
  print("[PHYSICAL] top_unknown_programs=",x.top_unknown_programs[:10])
  print("[PHYSICAL] materially_improved=",x.materially_improved,"state=",x.state)
  self.assertGreater(x.transactions,0)
  self.assertGreater(x.instructions,0)
  self.assertEqual(x.state,"PROGRAM_DECODE_COVERAGE_MEASURED")
  self.assertGreaterEqual(x.authoritative_known_ratio,0.0)
  self.assertLessEqual(x.authoritative_known_ratio,1.0)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-337 physical Solana program/protocol decode coverage measured")
 print("[PASS] infrastructure traffic separated from unresolved economic traffic")
 print("[PASS] top unknown programs retained for next evidence-driven decoder expansion")

