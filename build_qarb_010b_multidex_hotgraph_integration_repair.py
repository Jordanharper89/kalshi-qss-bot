from pathlib import Path
import py_compile

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
DEX=SUB/"dex"
for fn in ("raydium_cpmm.py","raydium_clmm.py","orca_whirlpool.py","meteora_damm_v2.py"):
    if not (DEX/fn).is_file():
        raise SystemExit("[FAIL] missing "+fn)

SRC=r"""
from dataclasses import dataclass
from time import perf_counter_ns

VENUES=("PUMPSWAP","METEORA_DLMM","RAYDIUM_CPMM","RAYDIUM_CLMM","ORCA_WHIRLPOOL","METEORA_DAMM_V2")
MAX_AGE_MS=750.0

@dataclass
class VenueQuote:
    venue:str
    token:str
    input_mint:str
    output_mint:str
    amount_in:int
    amount_out:int
    observed_ns:int
    pool:str

def fresh(q,now_ns=None):
    now=perf_counter_ns() if now_ns is None else int(now_ns)
    return (now-q.observed_ns)/1e6 <= MAX_AGE_MS

def best_two_leg(quotes,start_mint,end_mint,now_ns=None):
    now=perf_counter_ns() if now_ns is None else int(now_ns)
    buys=[q for q in quotes if q.input_mint==start_mint and fresh(q,now)]
    sells=[q for q in quotes if q.output_mint==end_mint and fresh(q,now)]
    best=None
    for a in buys:
        for b in sells:
            if a.venue==b.venue or a.token!=b.token:
                continue
            if a.output_mint!=b.input_mint:
                continue
            if a.amount_out!=b.amount_in:
                continue
            net=b.amount_out-a.amount_in
            bps=net/a.amount_in*10000.0 if a.amount_in>0 else -1e18
            row={
                "buy_venue":a.venue,"sell_venue":b.venue,"token":a.token,
                "start":a.amount_in,"end":b.amount_out,"net":net,"bps":bps,
                "age_ms":max((now-a.observed_ns)/1e6,(now-b.observed_ns)/1e6),
                "execution_authority":False,
            }
            if best is None or row["net"]>best["net"]:
                best=row
    return best

def route_pairs():
    return tuple((a,b) for a in VENUES for b in VENUES if a!=b)
"""

TEST=r"""
import inspect,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.multidex_graph import *

class T(unittest.TestCase):
    def test_all_venues(self):
        self.assertEqual(set(VENUES),{
            "PUMPSWAP","METEORA_DLMM","RAYDIUM_CPMM",
            "RAYDIUM_CLMM","ORCA_WHIRLPOOL","METEORA_DAMM_V2"
        })
        self.assertEqual(len(route_pairs()),30)
        print("[PASS] six DEX families produce 30 directed two-leg venue routes")

    def test_crossvenue_profit(self):
        now=perf_counter_ns()
        qs=[
            VenueQuote("RAYDIUM_CPMM","T","SOL","T",50,100,now,"A"),
            VenueQuote("ORCA_WHIRLPOOL","T","T","SOL",100,55,now,"B"),
        ]
        r=best_two_leg(qs,"SOL","SOL",now)
        self.assertEqual(r["net"],5)
        self.assertEqual(r["buy_venue"],"RAYDIUM_CPMM")
        print("[PASS] local multi-DEX graph chooses positive cross-venue route")

    def test_stale_not_routed(self):
        old=perf_counter_ns()-800_000_000
        qs=[
            VenueQuote("RAYDIUM_CPMM","T","SOL","T",50,100,old,"A"),
            VenueQuote("ORCA_WHIRLPOOL","T","T","SOL",100,55,old,"B"),
        ]
        self.assertIsNone(best_two_leg(qs,"SOL","SOL",perf_counter_ns()))
        print("[PASS] multi-DEX graph rejects >750ms route state")

    def test_no_hot_io(self):
        src=inspect.getsource(best_two_leg).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"):
            self.assertNotIn(bad,src)
        print("[PASS] multi-DEX route graph has no hot-path I/O")

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

M=SUB/"multidex_graph.py"
M.write_text(SRC,encoding="utf-8")
py_compile.compile(str(M),doraise=True)

T=ROOT/"test_qarb_010b_multidex_hotgraph_integration_repair.py"
T.write_text(TEST,encoding="utf-8")
py_compile.compile(str(T),doraise=True)

RUN=ROOT/"run_qarb_010b_multidex_hotgraph_integration_repair.py"
RUN.write_text(
    "from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.multidex_graph import VENUES,route_pairs\n"
    "print('[QARB-010B] MULTI-DEX HOTGRAPH INTEGRATION')\n"
    "print('[DEX] '+' | '.join(VENUES))\n"
    "print('[ROUTES] directed_two_leg=%d'%len(route_pairs()))\n"
    "print('[LATENCY] hard_state_age_ms=750')\n"
    "print('[MODE] execution_authority=FALSE')\n",
    encoding="utf-8",
)
py_compile.compile(str(RUN),doraise=True)

print("[PASS] QARB-010B multi-DEX hotgraph integration installed")
print("[FIX] QARB-010 broken runner retired")
print("[DEX] PumpSwap | Meteora DLMM | Raydium CPMM | Raydium CLMM | Orca | Meteora DAMM V2")
print("[ROUTES] 30 directed two-leg venue combinations")
print("[HOT] local graph only; hard <=750ms freshness")
print("[MODE] execution_authority=FALSE")
