import time,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine as e

class T(unittest.TestCase):
    def setUp(self):
        e._cross_cache={"at":0.0,"rows":[]}

    def test_no_dlmm_removed_before_quote_budget(self):
        old_raw,old_exact,old_disc=e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm
        e.raw_candidate_universe=lambda root:[
            {"token":"A","pump_pool":"PA","source":"LIVE_TAPE","age":None},
            {"token":"B","pump_pool":"PB","source":"LIVE_TAPE","age":None},
            {"token":"C","pump_pool":"PC","source":"LIVE_TAPE","age":None},
        ]
        e.exact_pool_ok=lambda t,p:(True,"OK")
        def disc(t):
            if t in ("A","B"):
                raise RuntimeError("NO_DLMM_PAIR")
            return {"address":"M","token_x":e.WSOL,"token_y":"C"}
        e.c.discover_dlmm=disc
        try:
            rows=e.candidate_universe(".")
        finally:
            e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm=old_raw,old_exact,old_disc
        self.assertEqual([x["token"] for x in rows],["C"])
        print("[PASS] NO_DLMM_PAIR removed before quote budget")

    def test_cache_prevents_repeat_discovery(self):
        old_raw,old_exact,old_disc=e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm
        calls={"n":0}
        e.raw_candidate_universe=lambda root:[{"token":"T","pump_pool":"P","source":"LIVE_TAPE","age":None}]
        e.exact_pool_ok=lambda t,p:(True,"OK")
        def disc(t):
            calls["n"]+=1
            return {"address":"M","token_x":e.WSOL,"token_y":"T"}
        e.c.discover_dlmm=disc
        try:
            a=e.candidate_universe(".")
            b=e.candidate_universe(".")
        finally:
            e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm=old_raw,old_exact,old_disc
        self.assertEqual(calls["n"],1)
        self.assertEqual(a,b)
        print("[PASS] crosslist cache prevents repeated discovery")

    def test_exact_wsol_pair_only(self):
        old_raw,old_exact,old_disc=e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm
        e.raw_candidate_universe=lambda root:[
            {"token":"T","pump_pool":"P","source":"LIVE_TAPE","age":None},
            {"token":"X","pump_pool":"PX","source":"LIVE_TAPE","age":None},
        ]
        e.exact_pool_ok=lambda t,p:(True,"OK")
        e.c.discover_dlmm=lambda t:(
            {"address":"M1","token_x":e.WSOL,"token_y":"T"} if t=="T"
            else {"address":"M2","token_x":"AAA","token_y":"BBB"}
        )
        try:
            rows=e.candidate_universe(".")
        finally:
            e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm=old_raw,old_exact,old_disc
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["token"],"T")
        print("[PASS] exact WSOL/token DLMM pair required")

    def test_429_stops_fanout_without_crash(self):
        import urllib.error
        old_raw,old_exact,old_disc=e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm
        e.raw_candidate_universe=lambda root:[
            {"token":"A","pump_pool":"PA","source":"LIVE_TAPE","age":None},
            {"token":"B","pump_pool":"PB","source":"LIVE_TAPE","age":None},
        ]
        e.exact_pool_ok=lambda t,p:(True,"OK")
        e.c.discover_dlmm=lambda t:(_ for _ in ()).throw(urllib.error.HTTPError("u",429,"rate",{},None))
        try:
            rows=e.candidate_universe(".")
        finally:
            e.raw_candidate_universe,e.exact_pool_ok,e.c.discover_dlmm=old_raw,old_exact,old_disc
        self.assertEqual(rows,[])
        print("[PASS] 429 halts discovery fanout cleanly")

    def test_max_tokens_applies_after_crosslist(self):
        old=e.MAX_TOKENS
        try:
            e.MAX_TOKENS=2
            e._cross_cache={"at":time.time(),"rows":[
                {"token":"A","pump_pool":"P","meteora_pool":"M","crosslisted":True},
                {"token":"B","pump_pool":"P","meteora_pool":"M","crosslisted":True},
                {"token":"C","pump_pool":"P","meteora_pool":"M","crosslisted":True},
            ]}
            rows=e.candidate_universe(".")
        finally:
            e.MAX_TOKENS=old
        self.assertEqual(len(rows),2)
        print("[PASS] quote budget applies after crosslist filtering")

if __name__=="__main__":
    unittest.main(verbosity=2)
