import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q
class T(unittest.TestCase):
    def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_existing_runner(self):
        self.assertIn("state=m.prepare(root)",inspect.getsource(q.p.serve).replace(" ",""))
    def test_install(self):
        q.install();self.assertIs(q.m.prepare,q.extended_prepare);self.assertIs(q.p._process_event,q.extended_process)
    def test_no_execution_submit(self):
        self.assertNotIn("sim_lane.submit(r)",inspect.getsource(q.extended_process))
if __name__=="__main__":unittest.main(verbosity=2)
