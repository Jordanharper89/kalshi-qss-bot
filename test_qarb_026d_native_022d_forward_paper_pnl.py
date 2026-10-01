import inspect,tempfile,unittest
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026d_native_022d_forward_paper_pnl as q

class FakeBook:
    def __init__(self,*a,**k):
        self.open={};self.rows=[];self.by_h={}
    def enter(self,pair,d,now):
        self.rows.append((pair,d,now))
        return SimpleNamespace(token=pair.token,size_sol=d["size_sol"],entry_quote_net_sol=d["net_sol"],
                               entry_quote_bps=d["net_bps"],entry_slot=7)
    def update_pair(self,pair,now): return []
    def persist(self): pass
    def summary(self): return {}

class T(unittest.TestCase):
    def test_exact_native_hook_contract(self):
        src=inspect.getsource(q.p._process_event)
        self.assertIn("sim_lane.submit(r)",src)
        self.assertIn("m.evaluate_token",src)
        print("[PASS] exact 022D qualified-signal hook physically exists")

    def test_submit_maps_hot_signal_without_sim(self):
        old=q.Book;q.Book=FakeBook
        try:
            pair=SimpleNamespace(token="T")
            state={"landing":0,"pairs":[pair],"preg":{}}
            lane=q.PaperLane(".",state)
            r={"token":"T","buy_venue":"PUMPSWAP","sell_venue":"METEORA_DLMM",
               "size_sol":1.4,"net_sol":0.02,"net_bps":142.0}
            pos=lane.submit(r)
            self.assertIsNotNone(pos)
            self.assertEqual(lane.entries,1)
        finally:q.Book=old
        print("[PASS] exact HOT_SIGNAL result redirects to paper entry")

    def test_serve_reuses_022d_transport(self):
        src=inspect.getsource(q.serve)
        for required in ("p.m.prepare","p.m._shards","p._worker","p._process_event"):
            self.assertIn(required,src)
        self.assertNotIn("SimulationLane(",src)
        self.assertNotIn("sim_lane.worker",src)
        print("[PASS] native 022D sharding/pricing reused; simulation lane absent")

    def test_no_execution(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        print("[PASS] PAPER_ONLY=True execution_authority=FALSE")

if __name__=="__main__":
    unittest.main(verbosity=2)
