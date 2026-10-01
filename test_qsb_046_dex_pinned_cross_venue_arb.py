import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.dex_pinned_cross_venue_arb import core as c

class T(unittest.TestCase):
    def test_quote_is_pinned_direct(self):
        seen={}
        def h(url,timeout):
            seen["url"]=url
            return {"outAmount":"1100","otherAmountThreshold":"1090","contextSlot":100,
                    "routePlan":[{"swapInfo":{"label":"Meteora DLMM","ammKey":"M","feeAmount":"1","feeMint":"X"}}]}
        q=c.quote(c.WSOL,"T",1000,"Meteora DLMM",h)
        self.assertEqual(q["dex"],"Meteora DLMM")
        self.assertIn("onlyDirectRoutes=true",seen["url"])
        self.assertIn("dexes=Meteora+DLMM",seen["url"])
        print("[PASS] quote hard-pinned to one direct DEX")

    def test_mismatch_rejected(self):
        def h(url,timeout):
            return {"outAmount":"1100","otherAmountThreshold":"1090","contextSlot":100,
                    "routePlan":[{"swapInfo":{"label":"Raydium CLMM"}}]}
        with self.assertRaises(RuntimeError): c.quote(c.WSOL,"T",1000,"Meteora DLMM",h)
        print("[PASS] DEX-label mismatch hard rejected")

    def test_buy_low_sell_high_math(self):
        calls=[]
        def h(url,timeout):
            calls.append(url)
            if len(calls)==1:
                return {"outAmount":"1000000","otherAmountThreshold":"997000","contextSlot":100,
                        "routePlan":[{"swapInfo":{"label":"Pump.fun Amm","ammKey":"P","feeAmount":"1","feeMint":"T"}}]}
            return {"outAmount":"10300000","otherAmountThreshold":"10290000","contextSlot":101,
                    "routePlan":[{"swapInfo":{"label":"Meteora DLMM","ammKey":"M","feeAmount":"1","feeMint":c.WSOL}}]}
        old=c.COST_LAMPORTS;c.COST_LAMPORTS=100000
        try:
            x=c.cross_venue("T",10000000,"Pump.fun Amm","Meteora DLMM",h)
            self.assertEqual(x["floor_net_lamports"],190000)
            self.assertTrue(x["qualified"])
        finally:c.COST_LAMPORTS=old
        print("[PASS] BUY low on DEX A / SELL high on DEX B qualifies after floor+costs")

    def test_same_dex_rejected(self):
        with self.assertRaises(ValueError):
            c.cross_venue("T",1000,"Raydium CLMM","Raydium CLMM",lambda u,t:{})
        print("[PASS] same-DEX roundtrip cannot masquerade as arbitrage")

    def test_labels(self):
        need={"Pump.fun Amm","Meteora DLMM","Meteora DAMM v2","Raydium CLMM","Raydium CP","Whirlpool"}
        self.assertTrue(need.issubset(set(c.DEXES)))
        print("[PASS] target DEX label registry present")

if __name__=="__main__": unittest.main(verbosity=2)
