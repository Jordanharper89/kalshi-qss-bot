import unittest,tempfile
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_multidex_hotgraph import engine as e
W=e.ANCHORS["So11111111111111111111111111111111111111112"]

def row(v,token,price,slot):
    # token -> WSOL, so price is WSOL/token
    return {"venue":v,"input_mint":token,"output_mint":"So11111111111111111111111111111111111111112",
            "input_amount":1000.0,"output_amount":1000.0*price,"slot":slot,"pool":v+"P"}

class T(unittest.TestCase):
    def test_all_target_venues_registered(self):
        self.assertEqual(e.TARGET_VENUES,{"PUMP_SWAP","METEORA_DLMM","METEORA_DAMM_V2","RAYDIUM_CLMM","RAYDIUM_CPMM","ORCA"})
        print("[PASS] all six observed Mriya-style DEX families are in one graph")

    def test_crossvenue_spread(self):
        rs=[row("PUMP_SWAP","T",.0010,100),row("METEORA_DLMM","T",.00105,101)]
        x=e.find_spreads(rs)[0]
        self.assertAlmostEqual(x["observed_spread_bps"],500,places=5)
        self.assertTrue(x["fresh"])
        print("[PASS] local graph detects fresh cross-venue spread without quote-endpoint fanout")

    def test_stale_not_fresh(self):
        rs=[row("RAYDIUM_CLMM","T",.0010,100),row("ORCA","T",.0011,104)]
        self.assertFalse(e.find_spreads(rs)[0]["fresh"])
        print("[PASS] >2-slot trade-price comparison cannot become hot signal")

    def test_cycle_no_network_fixture(self):
        rs=[row("RAYDIUM_CPMM","T",.0010,200),row("METEORA_DAMM_V2","T",.00104,201)]
        with tempfile.TemporaryDirectory() as td:
            out=e.cycle(td,lambda:({"rows":rs},rs))
            self.assertEqual(len(out["signals"]),1)
            self.assertFalse(out["execution_authority"])
            p=Path(td)/"runtime_state/qseries/qsb039_multidex_hotgraph/report.json"
            self.assertTrue(p.exists())
        print("[PASS] hot signal persisted read-only; no execution authority")

if __name__=="__main__":unittest.main(verbosity=2)
