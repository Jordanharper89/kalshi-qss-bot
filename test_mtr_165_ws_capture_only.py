import unittest
from unittest.mock import Mock
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_165_ws_capture_only as m
class Tests(unittest.TestCase):
    def test_no_wallet_no_run(self):
        m.main([])
    def test_forbidden_contract(self):
        with self.assertRaises(RuntimeError):m.forbidden()
    def test_callback_no_trade(self):
        cb=m.route_capture_cb("public","unused",{})
        lane=Mock()
        lane.newer_waiting.return_value=False
        counts={"positive_seen":0,"wrong_direction":0,"wrong_size":0}
        cb(lane,"token",{},{"direction":"METEORA_TO_PUMP","start":10000000},1,1,1)
        self.assertEqual(counts["wrong_direction"],1)
    def test_canonical_run_has_no_direct_signer(self):
        names=m.rt.run.__code__.co_names
        for name in ("signed_tx","send","keypair","simulate_current","compile_current"):
            self.assertNotIn(name,names)
    def test_original_functions_unchanged(self):
        original=m.rt.canonical_price
        m.main([])
        self.assertIs(m.rt.canonical_price,original)
if __name__=="__main__":unittest.main(verbosity=2)
