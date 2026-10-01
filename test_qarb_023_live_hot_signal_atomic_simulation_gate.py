import asyncio,unittest
from types import SimpleNamespace
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.live_atomic_simulation import SimulationLane,_bound_meta

class T(unittest.TestCase):
    def test_bound_meta_uses_live_pair(self):
        p=SimpleNamespace(meteora_pool="M",token_x="X",token_y="Y",decimals_x=9,decimals_y=6)
        m=_bound_meta(p)
        self.assertEqual(m["address"],"M");self.assertEqual(m["token_x"],"X")
        print("[PASS] atomic simulation binds exact live Meteora pool instead of rediscovery")

    def test_debounce_prevents_sim_storm(self):
        s=SimpleNamespace()
        lane=SimulationLane(".",s)
        sig={"token":"T","buy_pool":"P","sell_pool":"M","size_sol":1.0,
             "buy_venue":"PUMPSWAP","sell_venue":"METEORA_DLMM","net_sol":.1,"net_bps":100}
        self.assertTrue(lane.submit(sig));self.assertFalse(lane.submit(sig))
        print("[PASS] duplicate hot signals are debounced before RPC simulation")

    def test_unsupported_direction_not_queued(self):
        lane=SimulationLane(".",SimpleNamespace())
        sig={"token":"T","buy_pool":"P","sell_pool":"M","size_sol":1.0,
             "buy_venue":"METEORA_DLMM","sell_venue":"PUMPSWAP","net_sol":.1,"net_bps":100}
        self.assertFalse(lane.submit(sig))
        print("[PASS] unsupported reverse direction fails closed")

if __name__=="__main__":unittest.main(verbosity=2)
