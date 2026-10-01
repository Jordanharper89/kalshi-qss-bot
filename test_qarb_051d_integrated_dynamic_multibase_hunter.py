import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_051d_integrated_dynamic_multibase_hunter as q

class T(unittest.TestCase):
    def row(self,bps=100.0):
        return {"qualified":True,"route":"SOL>A>SOL","size_sol":.28,
                "net_sol":.01,"net_bps":bps}

    def test_same_generation_duplicate(self):
        g=q.GenerationEpisodeGate();g.begin_generation(1)
        self.assertIsNotNone(g.admit(self.row()))
        self.assertIsNone(g.admit(self.row()))
        self.assertEqual((g.raw_positive,g.duplicates,len(g.admitted)),(2,1,1))

    def test_material_reprice_is_new_episode(self):
        g=q.GenerationEpisodeGate();g.begin_generation(1)
        g.admit(self.row(100.0))
        self.assertIsNotNone(g.admit(self.row(106.0)))
        self.assertEqual(len(g.admitted),2)

    def test_absent_generation_closes_episode(self):
        g=q.GenerationEpisodeGate();g.begin_generation(1)
        g.admit(self.row());g.end_generation()
        g.begin_generation(2);g.end_generation()
        g.begin_generation(3)
        self.assertIsNotNone(g.admit(self.row()))
        self.assertEqual(len(g.admitted),2)

    def test_no_execution(self):
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":
    unittest.main(verbosity=2)
