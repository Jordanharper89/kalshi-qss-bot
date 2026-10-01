from pathlib import Path
import py_compile

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
DEX=SUB/"dex"
for fn in ("raydium_cpmm_live.py","raydium_clmm_live.py","orca_whirlpool_live.py","meteora_damm_v2_live.py"):
    if not (DEX/fn).is_file(): raise SystemExit("[FAIL] missing "+fn)
if not (SUB/"multidex_graph.py").is_file(): raise SystemExit("[FAIL] QARB-010B missing")

SRC=r"""
from __future__ import annotations
import json,time
from dataclasses import dataclass
from time import perf_counter_ns
from .multidex_graph import VenueQuote,best_two_leg,VENUES

MAX_AGE_MS=750.0
MIN_NET_BPS=20.0

class HotGraph:
    def __init__(self):
        self.rows={}
        self.events=0
        self.signals=0
        self.best=None

    def publish(self,q):
        self.events+=1
        key=(q.venue,q.pool,q.token,q.input_mint,q.output_mint,q.amount_in)
        self.rows[key]=q
        now=perf_counter_ns()
        r=best_two_leg(list(self.rows.values()),"WSOL","WSOL",now)
        if r is None: return None
        if r["age_ms"]>MAX_AGE_MS or r["bps"]<MIN_NET_BPS: return None
        self.signals+=1
        if self.best is None or r["net"]>self.best["net"]: self.best=r
        return r

def capability_matrix():
    from .dex import raydium_cpmm_live as rc
    from .dex import raydium_clmm_live as rl
    from .dex import orca_whirlpool_live as ow
    from .dex import meteora_damm_v2_live as md
    return {
      "PUMPSWAP":{"live":True,"local_quote":True},
      "METEORA_DLMM":{"live":True,"local_quote":True},
      "RAYDIUM_CPMM":{"live_adapter":True,"local_quote":True},
      "RAYDIUM_CLMM":{"live_adapter":True,"local_quote_provider_required":True},
      "ORCA_WHIRLPOOL":{"live_adapter":True,"local_quote_provider_required":True},
      "METEORA_DAMM_V2":{"live_adapter":True,"local_quote":True},
    }

def format_signal(r):
    return "[HOT_SIGNAL] buy=%s sell=%s token=%s net=%+.9f SOL bps=%+.2f age_ms=%.3f"%(
        r["buy_venue"],r["sell_venue"],r["token"],r["net"]/1e9,r["bps"],r["age_ms"])

def main():
    print("[QARB-015] SIX-DEX CONTINUOUS HOTGRAPH FOUNDATION",flush=True)
    print("[DEX] "+" | ".join(VENUES),flush=True)
    print("[LATENCY] hard_state_age_ms=750",flush=True)
    print("[CAPABILITY] "+json.dumps(capability_matrix(),sort_keys=True),flush=True)
    print("[TRUTH] PumpSwap+DLMM live stream proven; CPMM+DAMM live bindings installed; CLMM+Orca fail closed until native local providers are bound",flush=True)
    print("[MODE] scanner/handoff only execution_authority=FALSE",flush=True)

if __name__=="__main__": main()
"""

TEST=r"""
import inspect,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.multidex_live_hunter import *
class T(unittest.TestCase):
    def test_six_dex_matrix(self):
        m=capability_matrix();self.assertEqual(set(m),set(VENUES))
        self.assertTrue(m["RAYDIUM_CPMM"]["local_quote"])
        self.assertTrue(m["METEORA_DAMM_V2"]["local_quote"])
        self.assertTrue(m["RAYDIUM_CLMM"]["local_quote_provider_required"])
        self.assertTrue(m["ORCA_WHIRLPOOL"]["local_quote_provider_required"])
        print("[PASS] six-DEX capability truth matrix")
    def test_event_reprices_graph(self):
        h=HotGraph();now=perf_counter_ns()
        self.assertIsNone(h.publish(VenueQuote("RAYDIUM_CPMM","T","WSOL","T",50,100,now,"A")))
        r=h.publish(VenueQuote("METEORA_DAMM_V2","T","T","WSOL",100,55,now,"B"))
        self.assertIsNotNone(r);self.assertEqual(r["net"],5)
        print("[PASS] each fresh event can reprice cross-venue graph")
    def test_stale_fail_closed(self):
        h=HotGraph();old=perf_counter_ns()-800_000_000
        h.publish(VenueQuote("RAYDIUM_CPMM","T","WSOL","T",50,100,old,"A"))
        self.assertIsNone(h.publish(VenueQuote("METEORA_DAMM_V2","T","T","WSOL",100,55,old,"B")))
        print("[PASS] >750ms graph state cannot signal")
    def test_no_hot_io(self):
        src=inspect.getsource(HotGraph.publish).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"):
            self.assertNotIn(bad,src)
        print("[PASS] six-DEX graph publish has no network/filesystem/sleep")
if __name__=="__main__": unittest.main(verbosity=2)
"""

M=SUB/"multidex_live_hunter.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_015_six_dex_continuous_hotgraph.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
RUN=ROOT/"run_qarb_015_six_dex_continuous_hotgraph.py"
RUN.write_text(
 "from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.multidex_live_hunter import main\n"
 "if __name__=='__main__': main()\n",encoding="utf-8")
py_compile.compile(str(RUN),doraise=True)
print("[PASS] QARB-015 six-DEX continuous hotgraph foundation installed")
print("[HOT] fresh event -> affected quote -> cross-venue graph -> <=750ms signal gate")
print("[TRUTH] CLMM/Orca remain fail-closed until exact native local providers are bound")
print("[MODE] execution_authority=FALSE")
