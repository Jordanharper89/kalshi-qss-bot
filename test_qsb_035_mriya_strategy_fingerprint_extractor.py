import tempfile,unittest,json
from pathlib import Path
from urllib.error import HTTPError
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_strategy_fingerprint.extractor import route_chain,strategy_record,summarize,Fetcher

WSOL="So11111111111111111111111111111111111111112"
TOK="TOKEN"

def anatomy(sig="S",failed=False):
    legs=[
      {"resolved":True,"venue":"METEORA_DLMM","input_asset":WSOL,"input_amount":1.0,
       "output_asset":TOK,"output_amount":100.0},
      {"resolved":True,"venue":"PUMP_SWAP","input_asset":TOK,"input_amount":100.0,
       "output_asset":WSOL,"output_amount":1.02},
    ]
    return {"signature":sig,"slot":1,"failed":failed,"venues":["METEORA_DLMM","PUMP_SWAP"],
      "legs":legs,"fee_lamports":5000,"compute_units":100000,"wallet_sol_delta":-0.000005,
      "wallet_token_deltas":{WSOL:0.02},"wallet_anchor_deltas":{"WSOL":0.02,"SOL_NATIVE":-0.000005},
      "wallet_nonanchor_deltas":{},"closed_anchor_cycle":not failed,"resolved_legs":2,"leg_count":2,"error":None}

class T(unittest.TestCase):
    def test_closed_chain_return(self):
        c=route_chain(anatomy())
        self.assertTrue(c["contiguous"]);self.assertTrue(c["closed"]);self.assertAlmostEqual(c["gross_bps"],200,places=6)
        print("[PASS] exact resolved leg chain yields realized closed-loop gross bps")

    def test_sol_equivalent_net_subtracts_native_drag(self):
        r=strategy_record(anatomy())
        self.assertAlmostEqual(r["net_sol_equiv"],0.019995,places=12)
        print("[PASS] WSOL profit plus native SOL fee/rent drag yields exact SOL-equivalent net")

    def test_broken_chain_not_invented(self):
        a=anatomy();a["legs"][1]["input_asset"]="OTHER"
        c=route_chain(a);self.assertFalse(c["contiguous"]);self.assertIsNone(c.get("gross_bps"))
        print("[PASS] noncontiguous leg evidence cannot fabricate route return")

    def test_success_failure_family_stats(self):
        rs=[strategy_record(anatomy("W",False)),strategy_record(anatomy("F",True))]
        s=summarize(rs);self.assertEqual(s["samples"],2);self.assertEqual(s["wins"],1);self.assertEqual(s["fails"],1)
        self.assertAlmostEqual(s["win_rate"],.5)
        print("[PASS] wins and failed executor attempts remain in same route-family statistics")

    def test_429_retries_same_slot(self):
        calls={"n":0}
        def rpc(method,params,timeout):
            calls["n"]+=1
            if calls["n"]<3:raise HTTPError("x",429,"Too Many Requests",None,None)
            return {"blockTime":1,"transactions":[]}
        f=Fetcher(rpc=rpc,spacing=0,max_retries=4)
        # avoid real sleep in test by monkey-patching module time.sleep
        import qseries_v2.oracle_strategy_intelligence.solana_money.mriya_strategy_fingerprint.extractor as ex
        old=ex.time.sleep
        try:
            ex.time.sleep=lambda x:None
            b,n=f.fetch(123)
        finally:ex.time.sleep=old
        self.assertIsInstance(b,dict);self.assertEqual(n,3);self.assertEqual(f.rate_limits,2)
        print("[PASS] 429 backs off and retries same captured slot instead of abandoning it")

    def test_mixed_anchor_not_forced_into_sol(self):
        a=anatomy();a["wallet_anchor_deltas"]={"USDC":1.0,"SOL_NATIVE":-0.001}
        a["wallet_token_deltas"]={}
        r=strategy_record(a);self.assertIsNone(r["net_sol_equiv"])
        print("[PASS] mixed USDC/SOL result is not converted without an exact FX observation")

if __name__=="__main__":unittest.main(verbosity=2)
