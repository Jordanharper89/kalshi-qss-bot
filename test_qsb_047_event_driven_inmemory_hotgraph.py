import tempfile,time,unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.event_driven_hotgraph import core as c
SOL="So11111111111111111111111111111111111111112"
def row(f,a,b,ia,oa,t,s):
    return {"family":f,"input_asset":a,"output_asset":b,"input_amount":ia,"output_amount":oa,
            "observed_unix":t,"trade_signature":s,"strict_live_provenance":True}

class T(unittest.TestCase):
    def test_two_leg_crossvenue(self):
        t=100.0;g=c.HotGraph()
        rs=[row("PUMP_SWAP",SOL,"T",1,100,t,"1"),row("METEORA_DLMM","T",SOL,100,1.02,t+.1,"2")]
        g.ingest(rs,100.2);r,u=g.scan_changed({SOL,"T"},100.2)
        self.assertTrue(r);self.assertEqual(r[0]["legs"],2);self.assertGreater(r[0]["gross_bps"],190)
        print("[PASS] 2-leg cross-venue arbitrage trigger")
    def test_three_leg(self):
        t=200.0;g=c.HotGraph()
        rs=[row("RAYDIUM_CLMM",SOL,"A",1,10,t,"1"),row("ORCA","A","B",10,5,t+.1,"2"),
            row("METEORA_DLMM","B",SOL,5,1.03,t+.2,"3")]
        g.ingest(rs,200.3);r,u=g.scan_changed({SOL,"A","B"},200.3)
        self.assertTrue(any(x["legs"]==3 for x in r))
        print("[PASS] 3-leg triangular arbitrage trigger")
    def test_stale_rejected(self):
        g=c.HotGraph();g.ingest([row("PUMP_SWAP",SOL,"T",1,100,1,"1")],10)
        self.assertFalse(g.edges)
        print("[PASS] stale economics evicted")
    def test_file_change_only(self):
        with tempfile.TemporaryDirectory() as td:
            old=c.LIVE_PATHS;c.LIVE_PATHS=("x.json",)
            try:
                p=Path(td)/"x.json";p.write_text(json.dumps({"rows":[row("ORCA",SOL,"T",1,2,time.time(),"1")]}))
                st={};a,f=c.read_changed(td,st);b,f2=c.read_changed(td,st)
                self.assertEqual(len(a),1);self.assertFalse(b)
            finally:c.LIVE_PATHS=old
        print("[PASS] unchanged artifacts do not trigger recompute")
    def test_hot_recompute_latency(self):
        now=500.0;g=c.HotGraph()
        rs=[]
        for i in range(500):
            rs.append(row("PUMP_SWAP" if i%2==0 else "RAYDIUM_CPMM",SOL,f"T{i}",1,100+i,now,f"A{i}"))
        g.ingest(rs,now);_,u=g.scan_changed({SOL},now)
        self.assertLess(u,50000)
        print("[PASS] in-memory route recompute under 50ms fixture gate: %.1fus"%u)

if __name__=="__main__":unittest.main(verbosity=2)
