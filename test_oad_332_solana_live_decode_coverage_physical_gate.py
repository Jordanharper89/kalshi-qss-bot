\

import unittest
from qseries_v2.oracle_adapters.independent.oad_332_solana_live_decode_coverage_physical_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  x=measure_live_solana_decode_coverage(block_limit=1)
  print("[LIVE] blocks=",x.blocks,"transactions=",x.transactions,"instructions=",x.instructions)
  print("[LIVE] known_instruction_ratio=",x.known_instruction_ratio,"unknown_instructions=",x.unknown_instructions)
  print("[LIVE] dex_registry_pools=",x.dex_registry_pools,"dexes=",x.dex_registry_ids)
  print("[LIVE] dex_attributed_transactions=",x.dex_attributed_transactions,"wallet_flows=",x.wallet_flows)
  print("[LIVE] decoded_behaviors=",x.decoded_behaviors,"behavior_counts=",x.behavior_counts)
  print("[LIVE] top_unknown_programs=",x.unknown_program_counts[:10])
  self.assertGreater(x.transactions,0);self.assertGreater(x.instructions,0);self.assertGreater(x.dex_registry_pools,0)
  self.assertEqual(x.state,"LIVE_DECODE_COVERAGE_MEASURED")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-332 physical live Solana decode coverage measured")
 print("[PASS] unknown programs ranked for next decoder expansion instead of discarded")

