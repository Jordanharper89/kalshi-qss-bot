import inspect,unittest
from qseries_v2.oracle_execution import oracle_027_immutable_snapshot_generation_guard as q27

class Dummy:
    token="T";pump_pool="P";meteora_pool="M";token_x="X";token_y="Y"
    decimals_x=6;decimals_y=9;pump_base_reserve=11;pump_quote_reserve=22
    lb_bytes=b"abc";arrays=[(0,"A",b"one"),(1,"B",b"two")]
    last_slot=7;last_event_ns=8

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q27.EXECUTION_AUTHORITY)
        self.assertTrue(q27.PAPER_ONLY)
        self.assertFalse(q27.REAL_MONEY_MOVED)

    def test_raw_snapshot_copies_bytes(self):
        p=Dummy()
        s=q27.frozen_pair_snapshot(p)
        self.assertEqual(s["lb_bytes"],b"abc")
        self.assertEqual(s["arrays_raw"][0][2],b"one")
        self.assertNotIn("dlmm_state",s)

    def test_generation_guard_tracks_latest_submit(self):
        lane=q27.ImmutableLatestStateLane()
        lane.submit("T",{},1,1)
        first=lane.latest_generation["T"]
        lane.submit("T",{},2,2)
        self.assertTrue(lane.superseded("T",first))

    def test_end_guard_present(self):
        s=inspect.getsource(q27.ImmutableLatestStateLane._price)
        self.assertIn("ORACLE027_END_GENERATION_DROP",s)
        self.assertIn("self.superseded(token,generation)",s)

    def test_materialize_uses_poolstate_from_accounts(self):
        s=inspect.getsource(q27.materialize_snapshot)
        self.assertIn("PoolState.from_accounts",s)
        self.assertIn('snap["arrays_raw"]',s)

    def test_q20_seams_patched(self):
        s=inspect.getsource(q27.install)
        self.assertIn("q20._pair_snapshot=patched_pair_snapshot",s)
        self.assertIn("q20.LatestStateLane=ImmutableLatestStateLane",s)

    def test_no_execution(self):
        s=inspect.getsource(q27)
        self.assertNotIn("sendTransaction",s)
        self.assertNotIn("QSB_SOLANA_PRIVATE_KEY",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
