import inspect,unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_060_thesis_research_surface as m
class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(m.OIAR_060_BUILD_ID,"OIAR-060")
    def test_queries(self):
        self.assertTrue(m.is_thesis_query("what is the thesis for this market?"))
        self.assertTrue(m.is_thesis_query("why do you like this?"))
    def test_no_canonical_scan(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))
    def test_surface(self):
        x=m.render_thesis_surface();self.assertTrue(any("Probability: UNAVAILABLE" in s for s in x))
if __name__=="__main__":
    print("="*88);print(" OIAR-060 CERTIFICATION TEST");print(" THESIS RESEARCH SURFACE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] calibration-gated thesis surface certified");print("[DONE] OIAR-060 CERTIFIED")
