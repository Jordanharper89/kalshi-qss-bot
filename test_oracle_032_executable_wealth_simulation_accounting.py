import inspect, unittest
from unittest.mock import patch

from qseries_v2.oracle_execution import oracle_032_executable_wealth_simulation_accounting as q32

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q32.EXECUTION_AUTHORITY)
        self.assertTrue(q32.PAPER_ONLY)
        self.assertFalse(q32.REAL_MONEY_MOVED)

    def test_signer_prohibited(self):
        src=inspect.getsource(q32.keyless_measured_candidate)
        self.assertIn('raw=comp["unsigned"]',src)
        self.assertIn("sigverify=False",src)
        self.assertNotIn("q59.c.signed_tx(",src)
        self.assertNotIn(".sign_message(",src)

    def test_q88_wealth_primitive_reused(self):
        self.assertTrue(callable(q32.q88.simulate_wealth))
        src=inspect.getsource(q32.keyless_measured_candidate)
        self.assertIn("q88.simulate_wealth",src)

    def test_keyless_measured_profit(self):
        candidate={"name":"FULL","instructions":[],"pump_optional_removed":0}
        route={"start_lamports":1000}
        comp={
            "ok":True,
            "unsigned":b"x"*1200,
            "msg":b"m",
            "alts":[],
            "attempts":[],
        }
        sim={
            "err":None,
            "units":123,
            "gross_wealth_delta_lamports":20,
            "estimated_fee_lamports":5,
            "net_after_fee_lamports":15,
            "residual_token_delta_raw":0,
            "pre_native_lamports":1000,
            "post_native_lamports":1015,
            "pre_wsol_amount":0,
            "post_wsol_amount":0,
        }
        with patch.object(q32.q87,"compile_candidate",lambda *a,**k:comp), \
             patch.object(q32.q88,"simulate_wealth",lambda *a,**k:sim), \
             patch.object(q32.q59,"MIN_NET_BPS",1.0):
            row=q32.keyless_measured_candidate("U",route,candidate,[[]],"BH","T")
        self.assertTrue(row["profitable_after_fee"])
        self.assertEqual(row["net_sim_pnl_lamports"],15)
        self.assertEqual(row["residual_token_delta_raw"],0)

    def test_no_mriya_lookup(self):
        self.assertNotIn("recent_mriya_alt_keys",inspect.getsource(q32))

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction(",inspect.getsource(q32))

if __name__=="__main__":
    unittest.main(verbosity=2)
