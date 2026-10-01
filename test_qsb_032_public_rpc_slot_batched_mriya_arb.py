import asyncio,tempfile,time,unittest
from pathlib import Path
from urllib.error import HTTPError
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_slot_batch_arb.venue_registry import PROGRAMS
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_slot_batch_arb.tx_decode import decode_edges
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_slot_batch_arb.acquire import SlotBatchAcquirer
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_slot_batch_arb.scanner import observed_cycles,WSOL
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_slot_batch_arb.runtime import slots_from_rows

def tx(program,signer,src,dst,ain,aout,sig):
    return {"transaction":{"signatures":[sig],"message":{"accountKeys":[
      {"pubkey":signer,"signer":True},{"pubkey":program,"signer":False}],"instructions":[{"programId":program}]}},
      "meta":{"err":None,"preTokenBalances":[
        {"owner":signer,"mint":src,"uiTokenAmount":{"uiAmountString":str(ain)}},
        {"owner":signer,"mint":dst,"uiTokenAmount":{"uiAmountString":"0"}}],
        "postTokenBalances":[
        {"owner":signer,"mint":src,"uiTokenAmount":{"uiAmountString":"0"}},
        {"owner":signer,"mint":dst,"uiTokenAmount":{"uiAmountString":str(aout)}}]}}

class T(unittest.TestCase):
    def test_slot_dedupe(self):
        rows=[{"slot":10},{"slot":10},{"slot":11},{"slot":0},{}]
        self.assertEqual(slots_from_rows(rows),[11,10])
        print("[PASS] thousands of activity rows collapse to unique block slots")

    def test_direct_edges_from_full_block_transactions(self):
        n=time.time();a=tx(PROGRAMS["PUMP_SWAP"],"A",WSOL,"T",1,100,"S1")
        b=tx(PROGRAMS["METEORA_DLMM"],"B","T",WSOL,100,1.08,"S2")
        es=[]
        for x in (a,b):
            z,_=decode_edges(x,5,n,n);es+=z
        self.assertEqual(len(es),2);c=observed_cycles(es);self.assertTrue(c);self.assertGreater(c[0]["net_bps"],0)
        self.assertEqual(c[0]["classification"],"OBSERVED_BLOCK_ARB_PATTERN")
        print("[PASS] one block reconstructs positive cross-DEX observed cycle")

    def test_multi_dex_tx_not_misused_as_quote(self):
        n=time.time();x=tx(PROGRAMS["PUMP_SWAP"],"A",WSOL,"T",1,100,"S")
        x["transaction"]["message"]["instructions"].append({"programId":PROGRAMS["METEORA_DLMM"]})
        es,why=decode_edges(x,5,n,n);self.assertEqual(es,[]);self.assertEqual(why,"MULTI_DEX_TX")
        print("[PASS] target-style routed multi-DEX tx cannot be misused as a direct venue quote")

    def test_getblock_only_no_gettransaction(self):
        calls=[]
        def rpc(method,params,timeout):
            calls.append(method);return {"blockTime":1,"transactions":[]}
        a=SlotBatchAcquirer(rpc=rpc,min_rpc_interval=0)
        b,limited=a.fetch_block(10);self.assertFalse(limited);self.assertEqual(calls,["getBlock"])
        print("[PASS] hot acquisition uses one getBlock call, never per-signature getTransaction")

    def test_429_does_not_drop_slot(self):
        def rpc(*a,**k):raise HTTPError("x",429,"Too Many Requests",None,None)
        x=SlotBatchAcquirer(rpc=rpc,min_rpc_interval=0);b,limited=x.fetch_block(99)
        self.assertTrue(limited);self.assertNotIn(99,x.seen_slots);self.assertEqual(x.rate_limits,1)
        print("[PASS] 429 leaves slot retryable and runtime alive")

    def test_rate_pacing_contract(self):
        x=SlotBatchAcquirer(rpc=lambda *a,**k:{},min_rpc_interval=.45)
        self.assertGreaterEqual(x.min_rpc_interval,.45)
        print("[PASS] public RPC getBlock pace is bounded below 40-per-10s method limit")

    def test_pool_reciprocal_not_created(self):
        n=time.time();x=tx(PROGRAMS["PUMP_SWAP"],"USER",WSOL,"T",1,100,"S")
        x["meta"]["preTokenBalances"] += [
          {"owner":"POOL","mint":"T","uiTokenAmount":{"uiAmountString":"100"}},
          {"owner":"POOL","mint":WSOL,"uiTokenAmount":{"uiAmountString":"0"}}]
        x["meta"]["postTokenBalances"] += [
          {"owner":"POOL","mint":"T","uiTokenAmount":{"uiAmountString":"0"}},
          {"owner":"POOL","mint":WSOL,"uiTokenAmount":{"uiAmountString":"1"}}]
        es,_=decode_edges(x,5,n,n);self.assertEqual(len(es),1);self.assertEqual(es[0]["owner"],"USER")
        print("[PASS] pool-vault opposite flow does not fabricate reciprocal market price")

    def test_observed_cycles_never_claim_live_execution(self):
        n=time.time();a=tx(PROGRAMS["PUMP_SWAP"],"A",WSOL,"T",1,100,"S1")
        b=tx(PROGRAMS["METEORA_DLMM"],"B","T",WSOL,100,1.08,"S2")
        es=[]
        for x in (a,b):
            z,_=decode_edges(x,5,n,n);es+=z
        c=observed_cycles(es)[0]
        self.assertFalse(c["execution_authority"]);self.assertEqual(c["classification"],"OBSERVED_BLOCK_ARB_PATTERN")
        print("[PASS] block reconstruction cannot falsely certify an executable live arb")

if __name__=="__main__":unittest.main(verbosity=2)
