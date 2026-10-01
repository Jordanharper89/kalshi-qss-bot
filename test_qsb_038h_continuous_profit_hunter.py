import unittest,tempfile
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb import hunter

class T(unittest.TestCase):
    def test_summary_positive_candidate(self):
        r={"best":{"pre_sim_candidate":True,"token":"T","direction":"PUMP_TO_METEORA",
                   "pump_pool":"P","pool":"M","start_sol":.03,"end_sol":.0302,
                   "net_sol":.00019,"net_bps":63.3,"slot_spread":1,
                   "pump_transaction_present":True}}
        s=hunter.summarize(r)
        self.assertTrue(s["candidate"]);self.assertEqual(s["pump_pool"],"P")
        print("[PASS] qualifying 038G result becomes profit candidate")

    def test_summary_negative_rejected(self):
        r={"best":{"pre_sim_candidate":False,"token":"T","net_bps":-10,"slot_spread":1}}
        self.assertFalse(hunter.summarize(r)["candidate"])
        print("[PASS] losing/nonqualified route is never admitted")

    def test_loop_persists_candidate(self):
        calls={"n":0}
        def runner(root):
            calls["n"]+=1
            return {"best":{"pre_sim_candidate":True,"token":"T","direction":"METEORA_TO_PUMP",
              "pump_pool":"P","pool":"M","start_sol":.05,"end_sol":.0502,
              "net_sol":.00019,"net_bps":38.0,"slot_spread":1,"pump_transaction_present":True}}
        with tempfile.TemporaryDirectory() as td:
            st=hunter.run_loop(td,interval=0,max_cycles=1,runner=runner)
            p=Path(td)/"runtime_state/qseries/qsb038h_continuous_profit_hunter/candidates.jsonl"
            self.assertTrue(p.is_file());self.assertEqual(st["hits"],1)
        print("[PASS] positive candidate is captured to append-only ledger")

    def test_loop_does_not_persist_no_trade(self):
        def runner(root):
            return {"best":{"pre_sim_candidate":False,"token":"T","net_bps":5.0,"slot_spread":1}}
        with tempfile.TemporaryDirectory() as td:
            st=hunter.run_loop(td,interval=0,max_cycles=1,runner=runner)
            p=Path(td)/"runtime_state/qseries/qsb038h_continuous_profit_hunter/candidates.jsonl"
            self.assertFalse(p.exists());self.assertEqual(st["hits"],0)
        print("[PASS] nonqualified market state produces no candidate record")

    def test_execution_authority_false(self):
        import inspect
        s=Path(inspect.getfile(hunter)).read_text(encoding="utf-8")
        self.assertIn('"execution_authority":False',s)
        self.assertNotIn("sendTransaction",s)
        print("[PASS] continuous hunter cannot send live orders")

if __name__=="__main__":
    unittest.main(verbosity=2)
