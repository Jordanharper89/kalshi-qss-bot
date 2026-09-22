import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_063b_launchlab_universal_trade_normalizer import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_norm(self):
        p,d=write(ROOT)
        print("[STATE]",json.dumps({
            "exact_trade_count":d["exact_trade_count"],
            "revision":d["revision"]
        },sort_keys=True))
        for x in d["rows"]:
            print("[TRADE]",json.dumps(x,sort_keys=True))
        self.assertEqual(d["exact_trade_count"],4)
        self.assertTrue(all(x["side"]=="BUY" and x["effective_price"]>0 for x in d["rows"]))
        self.assertTrue(all(x["source_lineage"]["economics"]=="USLS_062C" for x in d["rows"]))
        self.assertFalse(d["profitability_claimed"])
        self.assertFalse(d["execution_authority"])
        print("[PASS] USLS-063B four exact LaunchLab trades normalized into universal trade tape")
        print("[PASS] lineage anchored to USLS-062C")
        print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    unittest.main()
