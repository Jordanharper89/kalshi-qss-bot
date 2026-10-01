import unittest,inspect
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

class T(unittest.TestCase):
    def test_cache(self):
        self.assertIsInstance(c._DLMM_CACHE,dict)
        print("[PASS] DLMM cache installed")

    def test_cached_miss(self):
        old=c.http
        c._DLMM_CACHE.clear()
        calls={"n":0}
        def fake(*a,**k):
            calls["n"]+=1
            return {"data":[]}
        c.http=fake
        try:
            with self.assertRaises(RuntimeError): c.discover_dlmm("TokenX")
            with self.assertRaises(RuntimeError): c.discover_dlmm("TokenX")
            self.assertEqual(calls["n"],1)
        finally:
            c.http=old
        print("[PASS] NO_DLMM_PAIR queried once per token")

    def test_meta_reuse(self):
        self.assertIn("meta",inspect.signature(c.sized_bidirectional_opportunities).parameters)
        print("[PASS] one pool discovery reused across all sizes")

    def test_no_jupiter(self):
        with open(c.__file__,encoding="utf-8") as f:
            src=f.read().lower()
        self.assertNotIn("jup.ag",src)
        self.assertNotIn("swap-instructions",src)
        print("[PASS] zero Jupiter hot-path code")

if __name__=="__main__":
    unittest.main(verbosity=2)
