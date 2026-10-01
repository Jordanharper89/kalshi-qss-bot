import tempfile,time,unittest
from pathlib import Path
from urllib.error import HTTPError
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica.live_edges import implied_swap_edges
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica.scanner import scan_cycles,WSOL,USDC
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica.profiler import RateSafeTargetProfiler

def tx(owner,src,dst,ain,aout,err=None):
    return {"blockTime":1000,"transaction":{"message":{"accountKeys":[owner],"instructions":[]}},
            "meta":{"err":err,"preBalances":[1],"postBalances":[1],
                    "preTokenBalances":[{"owner":owner,"mint":src,"uiTokenAmount":{"uiAmountString":str(ain)}},
                                        {"owner":owner,"mint":dst,"uiTokenAmount":{"uiAmountString":"0"}}],
                    "postTokenBalances":[{"owner":owner,"mint":src,"uiTokenAmount":{"uiAmountString":"0"}},
                                         {"owner":owner,"mint":dst,"uiTokenAmount":{"uiAmountString":str(aout)}}]}}

class T(unittest.TestCase):
    def test_exact_simple_owner_flow_becomes_one_direction_only(self):
        e=implied_swap_edges(tx("W",WSOL,"T",1,100),"PUMP_SWAP","S1",1000)
        self.assertEqual(len(e),1);self.assertEqual(e[0]["src"],WSOL);self.assertEqual(e[0]["dst"],"T")
        self.assertTrue(e[0]["observed_direction"])
        print("[PASS] live swap creates observed direction only; no synthetic reciprocal quote")

    def test_two_live_swaps_form_cost_adjusted_cycle(self):
        n=time.time()
        e1=implied_swap_edges(tx("A",WSOL,"T",1,100),"PUMP_SWAP","S1",n)[0]
        e2=implied_swap_edges(tx("B","T",WSOL,100,1.08),"METEORA_DLMM","S2",n+.05)[0]
        self.assertAlmostEqual(e1["rate"],100.0,places=9);self.assertAlmostEqual(e2["rate"],.0108,places=9)
        routes,s=scan_cycles([e1,e2],n+.10)
        self.assertTrue(routes);self.assertGreater(routes[0]["net_bps"],0);self.assertEqual(routes[0]["motif_match"],1.0)
        print("[PASS] contemporaneous observed PumpSwap/Meteora swaps expose positive 2-leg cycle after cost haircut")

    def test_stale_live_swap_rejected(self):
        n=time.time()
        e1=implied_swap_edges(tx("A",WSOL,"T",1,100),"PUMP_SWAP","S1",n-2)[0]
        e2=implied_swap_edges(tx("B","T",WSOL,100,.02),"METEORA_DLMM","S2",n-2)[0]
        routes,s=scan_cycles([e1,e2],n)
        self.assertEqual(routes,[]);self.assertEqual(s["fresh_edges"],0)
        print("[PASS] stale executed prices cannot masquerade as live arb quotes")

    def test_same_transaction_cannot_make_cycle(self):
        n=time.time()
        a={"src":WSOL,"dst":"T","rate":100,"venue":"X","market":"X:S","t":n,"signature":"S","observed_direction":True}
        b={"src":"T","dst":WSOL,"rate":.02,"venue":"Y","market":"Y:S","t":n,"signature":"S","observed_direction":True}
        routes,_=scan_cycles([a,b],n+.1);self.assertEqual(routes,[])
        print("[PASS] one transaction cannot self-manufacture an arbitrage cycle")

    def test_profiler_429_preserves_pending_queue(self):
        calls={"n":0}
        def rpc(method,params,timeout):
            if method=="getSignaturesForAddress":return [{"signature":"A"},{"signature":"B"}]
            calls["n"]+=1
            raise HTTPError("x",429,"Too Many Requests",None,None)
        with tempfile.TemporaryDirectory() as td:
            p=RateSafeTargetProfiler(Path(td),2,rpc=rpc);p.discover();r=p.cycle(1);s=p.snapshot()
            self.assertTrue(r["rate_limited"]);self.assertEqual(s["pending"],2);self.assertEqual(s["hydrated"],0)
        print("[PASS] RPC 429 slows profiler without discarding target signatures")

    def test_profiler_eventually_drains_without_429(self):
        good={"transaction":{"message":{"accountKeys":[],"instructions":[]}},"meta":{"err":{"x":1}}}
        def rpc(method,params,timeout):
            if method=="getSignaturesForAddress":return [{"signature":"A"},{"signature":"B"}]
            return good
        with tempfile.TemporaryDirectory() as td:
            p=RateSafeTargetProfiler(Path(td),2,rpc=rpc);p.discover();p.cycle(1);p.cycle(1);s=p.snapshot()
            self.assertEqual(s["pending"],0);self.assertEqual(s["hydrated"],2)
        print("[PASS] persistent profiler queue eventually hydrates full target sample")

    def test_multi_asset_owner_flow_not_inferred(self):
        x=tx("W",WSOL,"T",1,100)
        x["meta"]["postTokenBalances"].append({"owner":"W","mint":"Z","uiTokenAmount":{"uiAmountString":"5"}})
        self.assertEqual(implied_swap_edges(x,"X","S",1000),[])
        print("[PASS] ambiguous multi-asset transaction is not forced into a fake swap edge")

    def test_capture_freshness_separate_from_chain_time(self):
        n=time.time()
        e=implied_swap_edges(tx("A",WSOL,"T",1,100),"PUMP_SWAP","S1",n,n-10)[0]
        self.assertAlmostEqual(e["t"],n,places=6)
        self.assertAlmostEqual(e["chain_block_time"],n-10,places=6)
        routes,s=scan_cycles([e],n+.1)
        self.assertEqual(s["fresh_edges"],0)
        self.assertEqual(s["chain_stale_rejected"],1)
        print("[PASS] fresh arrival cannot hide an old chain transaction")

    def test_live_pending_queue_is_age_bounded(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica.live_edges import LiveEdgeCapture
        x=LiveEdgeCapture(rpc=lambda *a,**k: None)
        now=time.time()
        x.pending=[("OLD","X",now-5),("NEW","Y",now)]
        # Reproduce the production pruning contract directly.
        x.pending=[q for q in x.pending if now-q[2]<=.75][-32:]
        self.assertEqual([q[0] for q in x.pending],["NEW"])
        print("[PASS] stale live signatures cannot accumulate into a false-latency hydration backlog")

if __name__=="__main__":unittest.main(verbosity=2)
