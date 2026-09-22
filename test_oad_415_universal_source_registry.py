import unittest
from qseries_v2.oracle_adapters.independent.oad_415_universal_source_registry import *
class T(unittest.TestCase):
 def test_registry(self):
  r=registry_by_family('.'); self.assertTrue(r['NWS/NOAA'].active); self.assertFalse(r['REDDIT'].active); self.assertFalse(r['X/TWITTER'].active); self.assertFalse(r['NEWS'].active)
 def test_unique(self):
  x=build_source_registry('.'); self.assertEqual(len(x),len({a.source_family for a in x}))
if __name__=='__main__':unittest.main(verbosity=2)
