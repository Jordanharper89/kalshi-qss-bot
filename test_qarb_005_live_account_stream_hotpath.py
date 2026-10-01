import base64,inspect,struct,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as m

class Dummy:
    def __init__(self):
        self.token="T";self.pump_pool="P";self.meteora_pool="M"
        self.token_x=m.c.WSOL;self.token_y="T";self.decimals_x=9;self.decimals_y=6
        self.pump_base_vault="BV";self.pump_quote_vault="QV"
        self.pump_base_reserve=1000;self.pump_quote_reserve=2000
        self.lb_bytes=b"x";self.arrays=[(0,"A",b"a")]
        self.dlmm_state=object();self.last_slot=0;self.last_event_ns=0
    def watched_accounts(self):return ["BV","QV","M","A"]

class T(unittest.TestCase):
    def test_subscription_contract_processed(self):
        r=m.subscription_requests(["A","B"])
        self.assertEqual(len(r),2)
        self.assertTrue(all(x["method"]=="accountSubscribe" for x in r))
        self.assertTrue(all(x["params"][1]["commitment"]=="processed" for x in r))
        print("[PASS] hot accounts use processed accountSubscribe")

    def test_parse_notification(self):
        raw=b"abc"
        msg={"method":"accountNotification","params":{"subscription":7,"result":{
            "context":{"slot":123},"value":{"data":[base64.b64encode(raw).decode(),"base64"]}}}}
        ev=m.parse_account_notification(msg,{7:"ADDR"})
        self.assertEqual(ev["address"],"ADDR");self.assertEqual(ev["slot"],123);self.assertEqual(ev["raw"],raw)
        print("[PASS] websocket account notification parsed directly")

    def test_pump_vault_update_local_only(self):
        p=Dummy()
        raw=bytearray(72);struct.pack_into("<Q",raw,64,987654321)
        ok=m.apply_account_event(p,"PUMP_BASE","BV",bytes(raw),55,perf_counter_ns())
        self.assertTrue(ok);self.assertEqual(p.pump_base_reserve,987654321);self.assertEqual(p.last_slot,55)
        print("[PASS] Pump vault event updates in-memory reserve without RPC")

    def test_hot_event_has_no_io(self):
        src=inspect.getsource(m.hot_event_decision)+inspect.getsource(m.best_local_route)+inspect.getsource(m.apply_account_event)
        low=src.lower()
        for bad in ("rpc(","urllib","requests","open(","sleep(","subprocess","path("):
            self.assertNotIn(bad,low)
        print("[PASS] event->quote decision path has no REST/RPC/filesystem/sleep")

    def test_under_750_gate(self):
        p=Dummy()
        old=m.best_local_route
        m.best_local_route=lambda pair,landing:("PUMP_TO_METEORA",0.05,55_000_000,4_995_000,999.0)
        try:
            d=m.hot_event_decision(p,5000,perf_counter_ns())
        finally:
            m.best_local_route=old
        self.assertTrue(d["qualified"]);self.assertLess(d["event_to_decision_ms"],750)
        print("[PASS] fresh local event decision passes hard 750ms gate")

    def test_stale_event_rejected(self):
        p=Dummy()
        old=m.best_local_route
        m.best_local_route=lambda pair,landing:("PUMP_TO_METEORA",0.05,55_000_000,4_995_000,999.0)
        try:
            d=m.hot_event_decision(p,5000,perf_counter_ns()-800_000_000)
        finally:
            m.best_local_route=old
        self.assertFalse(d["qualified"])
        print("[PASS] event older than 750ms is rejected")

if __name__=="__main__":
    unittest.main(verbosity=2)
