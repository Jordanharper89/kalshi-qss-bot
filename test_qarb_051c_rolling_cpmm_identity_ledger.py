import tempfile,json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_051c_rolling_cpmm_identity_ledger as q

class T(unittest.TestCase):
    def test_accumulates_without_deleting(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/q.LEDGER;p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"rows":[{"pool":"P1","token_a":"A","token_b":"B","vault_a":"VA","vault_b":"VB"}]}))
            c=root/q.CAPTURE;c.parent.mkdir(parents=True,exist_ok=True)
            c.write_text(json.dumps({"rows":[]}))
            x=q.refresh(root)
            self.assertEqual(x["descriptor_count"],1)
            self.assertEqual(x["rows"][0]["pool"],"P1")
    def test_exact_layout(self):
        a=["0","1","2","POOL","US","UD","VA","VB","8","9","MA","MB","12"]
        d=q._descriptor_from_row({"venue":"RAYDIUM_CPMM","accounts":a,"slot":5})
        self.assertEqual((d["pool"],d["vault_a"],d["vault_b"],d["token_a"],d["token_b"]),
                         ("POOL","VA","VB","MA","MB"))
    def test_no_execution(self):
        self.assertTrue(q.READ_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":unittest.main(verbosity=2)
