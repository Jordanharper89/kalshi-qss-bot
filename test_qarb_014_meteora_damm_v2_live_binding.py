
import struct,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.meteora_damm_v2_live import *
class T(unittest.TestCase):
    def test_hydrate_update_quote(self):
        d=LivePool("P","A","B","V","W")
        def acct(addr):
            x=bytearray(72);struct.pack_into("<Q",x,64,1000 if addr=="V" else 2000);return bytes(x),1
        s=hydrate(d,acct)
        self.assertGreater(quote(s,"A",10),0)
        x=bytearray(72);struct.pack_into("<Q",x,64,1500)
        self.assertTrue(update(s,d,"V",bytes(x),perf_counter_ns()))
        self.assertEqual(s.reserve_a,1500)
        print("[PASS] Meteora DAMM V2 warm vaults -> live update -> local quote")
if __name__=="__main__": unittest.main(verbosity=2)
