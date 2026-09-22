import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_064b_raydium_strict_full_family_certification import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_final(self):
        p,d=write(ROOT)
        print("[STATE]",json.dumps({
            "strict_raydium_family_certified":d["strict_raydium_family_certified"],
            "raydium_family_boundary_closed":d["raydium_family_boundary_closed"],
            "phase4_status":d["phase4_status"],
            "next_boundary":d["next_boundary"]
        },sort_keys=True))

        for venue,state in d["matrix"].items():
            print("[RAYDIUM]",venue,json.dumps(state,sort_keys=True))

        self.assertTrue(d["strict_raydium_family_certified"],"RAYDIUM_FAMILY_NOT_STRICTLY_COMPLETE")
        self.assertTrue(d["raydium_family_boundary_closed"])
        self.assertEqual(d["next_boundary"],"METEORA_ORCA_SHARED_DECODER_PLUGINS")
        self.assertFalse(d["profitability_claimed"])
        self.assertFalse(d["execution_authority"])

        print("[PASS] USLS-064B strict Raydium full-family certification")
        print("[PASS] V4 + CPMM + CLMM + LaunchLab physically closed")
        print("[NEXT] METEORA_ORCA_SHARED_DECODER_PLUGINS")
        print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    unittest.main()
