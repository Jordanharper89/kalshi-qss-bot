import tempfile,unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_017b_ordered_physical_economic_resolution import EconomicResolution
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import persist_resolutions,read_resolution_dicts
class T(unittest.TestCase):
 def test_idempotent(self):
  with tempfile.TemporaryDirectory() as td:
   x=EconomicResolution("P","TARGET_FIRST","T",.1,.08,.12,.12,-.01,200,"RESOLVED",False)
   a=persist_resolutions((x,),td);b=persist_resolutions((x,),td)
   print("[SLOP-020]",a,b,read_resolution_dicts(td))
   self.assertEqual((a["new"],b["existing"]),(1,1));self.assertEqual(len(read_resolution_dicts(td)),1)
if __name__=="__main__":unittest.main(verbosity=2)
