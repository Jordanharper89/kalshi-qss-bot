import unittest,tempfile,pathlib,shutil
from qseries_v2.oracle_adapters.independent.oad_418_evidence_gap_priority_planner import *
class T(unittest.TestCase):
 def test_gap_rank(self):
  markets=[{'ticker':'E1','title':'Who wins the presidential election?'},{'ticker':'E2','title':'Will the election result be certified?'},{'ticker':'W','title':'Will temperature exceed 100 F?'}]
  x=rank_evidence_gaps(markets,'.'); self.assertTrue(x); self.assertEqual(x[0].source_family,'ELECTION_OFFICIAL'); self.assertGreaterEqual(x[0].affected_markets,2)
 def test_read_only(self): self.assertTrue(READ_ONLY); self.assertFalse(EXECUTION_AUTHORITY)
if __name__=='__main__':unittest.main(verbosity=2)
