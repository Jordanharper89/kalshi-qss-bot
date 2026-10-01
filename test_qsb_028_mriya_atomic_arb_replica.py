import tempfile,time,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica.profile import *
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica.scanner import scan_cycles,WSOL,USDC
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica.profiler import classify_target_transaction
import qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica.persistence as ps

def edge(src,dst,rate,venue,market,t):
    return {"src":src,"dst":dst,"rate":rate,"venue":venue,"market":market,"t":t,"slot":1,"id":market,"source":"FIX"}

class T(unittest.TestCase):
    def test_target_evidence_is_atomic_arb(self):
        self.assertEqual(TARGET_EVIDENCE["strategy_class"],"ATOMIC_MULTI_DEX_ARBITRAGE")
        self.assertGreater(TARGET_EVIDENCE["mev_live_24h_net_usd"],0)
        self.assertGreaterEqual(len(OBSERVED_POSITIVE_EXAMPLES),6)
        print("[PASS] target wallet evidence frozen as profitable historical atomic-arb behavior")

    def test_two_leg_meteora_pumpswap_cycle(self):
        n=time.time();tok="TOKEN"
        es=[edge(WSOL,tok,100,"PUMP_SWAP","P1",n),edge(tok,WSOL,.0105,"METEORA_DLMM","M1",n+.05)]
        x=scan_cycles(es,n+.10)
        self.assertTrue(x);self.assertEqual(x[0]["hops"],2);self.assertGreater(x[0]["net_bps"],0)
        self.assertEqual(x[0]["motif_match"],1.0)
        print("[PASS] exact observed Meteora-DLMM/PumpSwap 2-leg motif detected net-positive after modeled costs")

    def test_four_leg_observed_family(self):
        n=time.time();a,b,c="A","B","C"
        es=[edge(USDC,a,2,"RAYDIUM_CPMM","R1",n),edge(a,b,2,"RAYDIUM_CLMM","R2",n+.05),
            edge(b,c,2,"ORCA_WHIRLPOOLS","O1",n+.08),edge(c,USDC,.13,"METEORA_DLMM","M1",n+.10)]
        x=scan_cycles(es,n+.15);self.assertTrue(any(o["hops"]==4 and o["motif_match"]==1 for o in x))
        print("[PASS] observed 4-venue Raydium/Raydium/Orca/Meteora cycle family detected")

    def test_stale_edges_cannot_fake_profit(self):
        n=time.time();tok="T"
        es=[edge(WSOL,tok,100,"PUMP_SWAP","P1",n-3),edge(tok,WSOL,.02,"METEORA_DLMM","M1",n-3)]
        self.assertEqual(scan_cycles(es,n),[])
        print("[PASS] stale artifact prices cannot manufacture a live arbitrage")

    def test_unprofitable_cycle_rejected(self):
        n=time.time();tok="T"
        es=[edge(WSOL,tok,100,"PUMP_SWAP","P1",n),edge(tok,WSOL,.0099,"METEORA_DLMM","M1",n)]
        self.assertEqual(scan_cycles(es,n+.1),[])
        print("[PASS] route must remain positive after per-leg haircut and landing-cost buffer")

    def test_target_tx_classifier_rejects_directional_inventory(self):
        tx={"transaction":{"message":{"accountKeys":[TARGET_WALLET,TARGET_EXECUTOR_PROGRAM],"instructions":[{"programId":TARGET_EXECUTOR_PROGRAM}]}},
            "meta":{"err":None,"preBalances":[1000000000,0],"postBalances":[1100000000,0],"fee":5000,
                    "preTokenBalances":[],"postTokenBalances":[{"owner":TARGET_WALLET,"mint":"MEME","uiTokenAmount":{"uiAmountString":"10"}}]}}
        c=classify_target_transaction(tx);self.assertFalse(c["atomic_arb_candidate"]);self.assertIn("MEME",c["nonanchor_delta"])
        print("[PASS] target profiler distinguishes atomic arb from directional token inventory")

    def test_target_tx_classifier_accepts_closed_cycle(self):
        tx={"transaction":{"message":{"accountKeys":[TARGET_WALLET,TARGET_EXECUTOR_PROGRAM],"instructions":[{"programId":TARGET_EXECUTOR_PROGRAM}]}},
            "meta":{"err":None,"preBalances":[1000000000,0],"postBalances":[1100000000,0],"fee":5000,
                    "preTokenBalances":[],"postTokenBalances":[]}}
        c=classify_target_transaction(tx);self.assertTrue(c["atomic_arb_candidate"]);self.assertGreater(c["anchor_delta"]["SOL_NATIVE"],0)
        print("[PASS] target profiler accepts executor-backed positive closed SOL cycle")

    def test_onedrive_persistence_denial_survives(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.json";old=ps.os.replace
            try:
                ps.os.replace=lambda a,b: (_ for _ in ()).throw(PermissionError(5,"denied"))
                r=ps.write_json(p,{"x":1})
            finally:ps.os.replace=old
            self.assertTrue(r["ok"])
        print("[PASS] OneDrive replace denial cannot kill arb state")

    def test_execution_stays_false(self):
        x=OBSERVED_POSITIVE_EXAMPLES[0];self.assertGreater(x["net_usd"],0)
        # Historical target profitability does not authorize Q Series execution.
        from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_atomic_arb_replica import EXECUTION_AUTHORITY
        self.assertFalse(EXECUTION_AUTHORITY)
        print("[PASS] historically profitable target evidence does not bypass execution gate")

if __name__=="__main__":unittest.main(verbosity=2)
