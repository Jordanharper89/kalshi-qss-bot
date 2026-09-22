import unittest
from qseries_v2.oracle_adapters.independent.oad_414_oracle_source_capability_inventory import *
class T(unittest.TestCase):
 def test_inventory(self):
  x=inventory_source_capabilities('.'); self.assertTrue(x); self.assertTrue(any(a.source_family=='NWS/NOAA' for a in x)); self.assertTrue(any(a.source_family=='COINBASE' for a in x))
 def test_read_only(self): self.assertTrue(READ_ONLY); self.assertFalse(EXECUTION_AUTHORITY); self.assertFalse(PROBABILITY_ENABLED)
if __name__=='__main__':unittest.main(verbosity=2)
