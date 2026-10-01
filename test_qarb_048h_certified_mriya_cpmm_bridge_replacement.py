import tempfile,json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex import raydium_cpmm_mriya_bridge as q

class T(unittest.TestCase):
    def test_exact_mriya_layout(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/q.MRIYA_CAPTURE;p.parent.mkdir(parents=True)
            acc=["AUTH","CONFIG","OBS","POOL","US","UD","VA","VB","TPA","TPB","MA","MB","OBS2"]
            p.write_text(json.dumps({"rows":[{"venue":"RAYDIUM_CPMM","program_id":q.CPMM_PROGRAM,"accounts":acc}]}))
            rows=q._from_mriya_capture(root)
            self.assertEqual(len(rows),1)
            self.assertEqual((rows[0].pool,rows[0].vault_a,rows[0].vault_b),("POOL","VA","VB"))
            self.assertEqual((rows[0].token_a,rows[0].token_b),("MA","MB"))
    def test_short_layout_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/q.MRIYA_CAPTURE;p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"venue":"RAYDIUM_CPMM","accounts":["x"]}))
            self.assertEqual(q._from_mriya_capture(root),[])
    def test_reuses_base_live_math(self):
        self.assertIs(q.hydrate,q.base.hydrate)
        self.assertIs(q.update,q.base.update)
        self.assertIs(q.quote,q.base.quote)
    def test_no_execution(self):
        self.assertTrue(q.READ_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)

if __name__=="__main__":unittest.main(verbosity=2)
