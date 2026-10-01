import unittest,tempfile
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import core
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import crosslisted as x

class T(unittest.TestCase):
    def test_certified_identity_rows_key_is_consumed(self):
        fake_capture={"rows":[{"venue":"PUMP_SWAP","event":{"pool":"PP1"}}]}
        fake_resolve={"identity_rows":[
            {"venue":"PUMP_SWAP","identity_state":"EXACT","pool":"PP1",
             "base_mint":"TOK","quote_mint":core.WSOL,
             "base_decimals":6,"quote_decimals":9}]}
        async def cap(seconds=5,max_rows=1600): return fake_capture
        import types,sys
        m1=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router")
        m1.capture=cap
        m2=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver")
        m2.resolve=lambda root:fake_resolve
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(sys.modules,{m1.__name__:m1,m2.__name__:m2}):
                r=x.live_pumpswap_identities(td,1)
        self.assertEqual(len(r["identities"]),1)
        self.assertEqual(r["identities"][0]["token"],"TOK")
        self.assertEqual(r["resolver_identity_rows"],1)
        self.assertEqual(r["active_overlap"],1)
        print("[PASS] certified USLS-047C identity_rows are now consumed")

    def test_nonactive_identity_is_not_admitted(self):
        fake_capture={"rows":[{"venue":"PUMP_SWAP","event":{"pool":"ACTIVE"}}]}
        fake_resolve={"identity_rows":[
            {"venue":"PUMP_SWAP","identity_state":"EXACT","pool":"OTHER",
             "base_mint":"TOK","quote_mint":core.WSOL,
             "base_decimals":6,"quote_decimals":9}]}
        async def cap(seconds=5,max_rows=1600): return fake_capture
        import types,sys
        m1=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router");m1.capture=cap
        m2=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver");m2.resolve=lambda root:fake_resolve
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(sys.modules,{m1.__name__:m1,m2.__name__:m2}):
                r=x.live_pumpswap_identities(td,1)
        self.assertEqual(r["active_overlap"],0)
        self.assertEqual(r["identities"],[])
        print("[PASS] stale/nonactive pool identity cannot enter current intersection")

    def test_diagnostic_fields_exist(self):
        fake_capture={"rows":[]}
        fake_resolve={"identity_rows":[]}
        async def cap(seconds=5,max_rows=1600): return fake_capture
        import types,sys
        m1=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router");m1.capture=cap
        m2=types.ModuleType("qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver");m2.resolve=lambda root:fake_resolve
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(sys.modules,{m1.__name__:m1,m2.__name__:m2}):
                r=x.live_pumpswap_identities(td,1)
        self.assertIn("resolver_identity_rows",r)
        self.assertIn("active_overlap",r)
        print("[PASS] zero-result diagnostics distinguish capture/resolver/overlap")

if __name__=="__main__":
    unittest.main(verbosity=2)
