import unittest,tempfile
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_executable_requote import gate as g

class T(unittest.TestCase):
    def test_two_leg_profitable_requote(self):
        route={"path":["A","T","A"],"legs":2,"venues":["PUMP_SWAP","METEORA_DLMM"]}
        def h(url,timeout):
            if "inputMint=A" in url:return {"outAmount":"1100","transaction":"x","requestId":"1"}
            return {"outAmount":"1030","transaction":"y","requestId":"2"}
        x=g.requote_route(route,1000,http=h)
        self.assertAlmostEqual(x["net_bps"],300,places=6);self.assertTrue(x["qualified"])
        print("[PASS] 2-leg route survives executable Jupiter transaction re-quote")

    def test_three_leg_profitable_requote(self):
        route={"path":["A","X","Y","A"],"legs":3,"venues":["A","B","C"]}
        vals=iter([1200,900,1050])
        def h(url,timeout):return {"outAmount":str(next(vals)),"transaction":"x","requestId":"r"}
        x=g.requote_route(route,1000,http=h)
        self.assertAlmostEqual(x["net_bps"],500,places=6)
        print("[PASS] 3-leg route re-quoted leg-by-leg with executable payload presence")

    def test_missing_tx_fails_qualification(self):
        route={"path":["A","T","A"],"legs":2,"venues":["A","B"]}
        vals=iter([
          {"outAmount":"1100","transaction":None,"requestId":"1"},
          {"outAmount":"1200","transaction":"y","requestId":"2"}])
        def h(url,timeout):return next(vals)
        x=g.requote_route(route,1000,http=h)
        self.assertFalse(x["qualified"])
        print("[PASS] missing executable transaction hard-rejects qualification")

    def test_authority_false(self):
        route={"path":["A","T","A"],"legs":2,"venues":["A","B"]}
        vals=iter([{"outAmount":"1001","transaction":"x","requestId":"1"},{"outAmount":"1002","transaction":"y","requestId":"2"}])
        def h(url,timeout):return next(vals)
        x=g.requote_route(route,1000,http=h)
        self.assertFalse(x["execution_authority"]);self.assertFalse(x["atomic_composer_present"])
        print("[PASS] no false atomic/execution claim")

if __name__=="__main__":unittest.main(verbosity=2)
