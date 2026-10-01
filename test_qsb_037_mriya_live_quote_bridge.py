import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_live_quote_bridge.runtime import _template,WSOL,TARGET_TOKEN

def rec(sig,start,bps):
    out=start*(1+bps/10000)
    return {"signature":sig,"failed":False,"venue_chain":["METEORA_DLMM","PUMP_SWAP"],"fee_sol":.000005,
      "chain":{"closed":True,"contiguous":True,"gross_bps":bps,"start_amount":start,"legs":[
        {"input_asset":WSOL,"output_asset":TARGET_TOKEN},{"input_asset":TARGET_TOKEN,"output_asset":WSOL,"output_amount":out}]}}
class T(unittest.TestCase):
    def test_exact_target_template_loaded(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runtime_state/qseries/qsb035_mriya_strategy_fingerprint/report.json";p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"records":[rec("A",.699517,96.31),rec("B",1.74628,118.37)]}))
            t=_template(td);self.assertIsNotNone(t);self.assertEqual(t["wins"],2)
            self.assertAlmostEqual(t["historical_avg_gross_bps"],107.34,places=2)
        print("[PASS] QSB-037 consumes only exact repeated DLMM->PumpSwap Mriya template")
    def test_decimal_anomaly_not_template(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runtime_state/qseries/qsb035_mriya_strategy_fingerprint/report.json";p.parent.mkdir(parents=True)
            bad=rec("X",1,1000000);good=rec("A",1,100)
            p.write_text(json.dumps({"records":[bad,good]}))
            self.assertIsNone(_template(td))
        print("[PASS] absurd decimal route cannot satisfy live quote template gate")
    def test_bridge_contains_official_quote_calls(self):
        import inspect
        import qseries_v2.oracle_strategy_intelligence.solana_money.mriya_live_quote_bridge.runtime as r
        b=Path(inspect.getfile(r)).parent/"node_bridge/quote_bridge.mjs"
        s=b.read_text()
        self.assertIn("pool.swapQuote",s);self.assertIn("OnlinePumpAmmSdk",s);self.assertIn("sellBaseInput",s)
        self.assertIn("slotSpread<=2",s)
        print("[PASS] generated bridge binds official Meteora swapQuote + PumpSwap sellBaseInput with slot spread gate")
    def test_no_execution_authority(self):
        import qseries_v2.oracle_strategy_intelligence.solana_money.mriya_live_quote_bridge as q
        self.assertFalse(q.EXECUTION_AUTHORITY);self.assertTrue(q.PAPER_ONLY)
        print("[PASS] quote bridge remains paper-only with execution authority false")
if __name__=="__main__":unittest.main(verbosity=2)
