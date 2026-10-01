import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062a_mriya_six_dex_router as q
class T(unittest.TestCase):
 def test_aliases(self):
  for x in ("PUMPSWAP","METEORA_DLMM","RAYDIUM_CPMM","METEORA_DAMM_V2","RAYDIUM_CLMM","ORCA_WHIRLPOOL"):self.assertIn(x,q.ALIASES.values())
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
