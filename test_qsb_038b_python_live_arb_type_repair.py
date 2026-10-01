import sys,types,unittest
from unittest.mock import patch
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import core

class FakeQuote:
    complete=True
    remaining_in=0
    amount_out=123456789
    bins_crossed=2

class FakePoolState:
    @staticmethod
    def from_accounts(lb,bins,decimals_x,decimals_y,lb_pair_key=None,exhaustive=False):
        if isinstance(lb_pair_key,str):
            raise TypeError("string argument without an encoding")
        assert lb==b"LB"
        assert bins==[b"BIN"]
        assert exhaustive is True
        return object()

def fake_quote(*a,**k):
    return FakeQuote()

class T(unittest.TestCase):
    def test_exact_crash_is_removed(self):
        fake=types.ModuleType("meteora_dlmm")
        fake.PoolState=FakePoolState
        fake.quote=fake_quote
        meta={"address":"BASE58_POOL_STRING","decimals_x":9,"decimals_y":6,
              "token_x":core.WSOL,"token_y":core.TOKEN}
        with patch.dict(sys.modules,{"meteora_dlmm":fake}):
            with patch.object(core,"fetch_account_bytes",return_value=b"LB"):
                with patch.object(core,"fetch_bin_arrays",return_value=[b"BIN"]):
                    q=core.meteora_quote("rpc",meta,0.699517207)
        self.assertTrue(q["exact"])
        self.assertEqual(q["raw_out"],123456789)
        print("[PASS] reproduced QSB-038 Meteora call without Base58-string lb_pair_key TypeError")

    def test_source_never_passes_pool_string_as_lb_pair_key(self):
        import inspect
        s=open(inspect.getfile(core),encoding="utf-8").read()
        self.assertNotIn('lb_pair_key=pool_meta["address"]',s)
        print("[PASS] Base58 pool string is no longer passed to 32-byte lb_pair_key")

    def test_original_qsb038_gate_preserved(self):
        self.assertEqual(core.MIN_NET_BPS,10.0)
        self.assertEqual(core.MAX_SLOT_SPREAD,4)
        print("[PASS] QSB-038 paper-profit gates preserved")

if __name__=="__main__":
    unittest.main(verbosity=2)
