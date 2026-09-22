import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_124_authoritative_sports_reasoning_comparison_input import build_sports_reasoning_comparison_inputs

class T(unittest.TestCase):
    def test_grouping(self):
        e1=SimpleNamespace(market_id="KX1",source_id="source.independent.mlb:game:1",independent_evidence=True,candidate_only=True,direction=None,probability=None)
        e2=SimpleNamespace(market_id="KX1",source_id="source.independent.mlb:game:2",independent_evidence=True,candidate_only=True,direction=None,probability=None)
        r=build_sports_reasoning_comparison_inputs((e1,e2))
        print("[MARKETS]",len(r))
        print("[EVIDENCE_COUNT]",r[0].evidence_count)
        print("[INDEPENDENT_SOURCES]",r[0].independent_source_ids)
        self.assertEqual(len(r),1)
        self.assertEqual(r[0].evidence_count,2)
        self.assertIsNone(r[0].direction)
        self.assertIsNone(r[0].probability)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-124 authoritative sports reasoning comparison input certified")
