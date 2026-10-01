import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money import qsb058_gav_profitable_case as q

class T(unittest.TestCase):
    def test_exact_four_point_replay(self):
        rows=q.replay_observed()
        self.assertEqual(len(rows),4)
        self.assertTrue(all(x["profitable"] for x in rows))
        self.assertAlmostEqual(rows[-1]["net_sol"],0.004280742,places=9)
        self.assertLess(max(x["replay_bps"] for x in rows)-min(x["replay_bps"] for x in rows),4.0)
        print("[PASS] exact QSB-055 four-point profitable curve frozen and replayed")

    def test_prefix_resolution_unique(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/q.TAPE;p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"rows":[
              {"venue":"PUMP_SWAP","token_address":"GavQxkBXLgFULLTOKEN","market_address":"PUMPPOOL","slot":10},
              {"venue":"PUMP_SWAP","token_address":"OTHER","market_address":"OTHERPOOL","slot":11}
            ]}),encoding="utf-8")
            x=q.resolve_case(td)
            self.assertTrue(x["resolved"])
            self.assertEqual(x["token"],"GavQxkBXLgFULLTOKEN")
            self.assertEqual(x["pump_pool"],"PUMPPOOL")
        print("[PASS] truncated runtime token is deterministically resolved from production tape")

    def test_report_preserves_execution_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/q.TAPE;p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"rows":[]}),encoding="utf-8")
            r,out=q.build_report(td)
            self.assertFalse(r["execution_authority"])
            self.assertFalse(r["real_money_moved"])
            self.assertIn("QSB_059_PUMP_TO_METEORA_NATIVE_ATOMIC_COMPOSER",r["next_required_boundary"])
            self.assertTrue(out.is_file())
        print("[PASS] QSB-058 freezes evidence and hands off exact reverse atomic composer boundary")

if __name__=="__main__":
    unittest.main(verbosity=2)
