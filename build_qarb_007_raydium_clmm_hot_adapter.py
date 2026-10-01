from pathlib import Path
import py_compile
ROOT=Path.cwd()
DEX=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/dex"
if not (DEX/"raydium_cpmm.py").is_file(): raise SystemExit("[FAIL] QARB-006 missing")
SRC=r"""
from dataclasses import dataclass
from time import perf_counter_ns

VENUE="RAYDIUM_CLMM"
MAX_AGE_MS=750.0

@dataclass
class PoolState:
    pool:str
    token_a:str
    token_b:str
    local_quote_fn:object
    observed_ns:int

    def fresh(self,now_ns=None,max_age_ms=MAX_AGE_MS):
        now=perf_counter_ns() if now_ns is None else int(now_ns)
        return (now-self.observed_ns)/1e6 <= float(max_age_ms)

def bind_local_quoter(pool,token_a,token_b,quote_fn,observed_ns=None):
    if not callable(quote_fn): raise RuntimeError("LOCAL_QUOTER_REQUIRED")
    return PoolState(pool,token_a,token_b,quote_fn,
        perf_counter_ns() if observed_ns is None else int(observed_ns))

def quote_exact_in(state,input_mint,amount_in,now_ns=None):
    if not state.fresh(now_ns): raise RuntimeError("STALE_RAYDIUM_CLMM")
    if input_mint not in (state.token_a,state.token_b): raise RuntimeError("MINT_NOT_IN_POOL")
    out=state.local_quote_fn(input_mint,int(amount_in))
    if not isinstance(out,int) or out<0: raise RuntimeError("BAD_LOCAL_QUOTE")
    return out

def touch(state,observed_ns):
    state.observed_ns=int(observed_ns);return state
"""
TEST=r"""
import inspect,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.raydium_clmm import *
class T(unittest.TestCase):
    def test_local_quoter_bridge(self):
        s=bind_local_quoter("P","SOL","T",lambda mint,x:x*2)
        self.assertEqual(quote_exact_in(s,"SOL",7),14)
        print("[PASS] Raydium CLMM repo-native local quoter bridge")
    def test_stale(self):
        s=bind_local_quoter("P","SOL","T",lambda m,x:x,perf_counter_ns()-800_000_000)
        with self.assertRaisesRegex(RuntimeError,"STALE"): quote_exact_in(s,"SOL",1)
        print("[PASS] Raydium CLMM >750ms state rejected")
    def test_no_adapter_io(self):
        src=inspect.getsource(quote_exact_in).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"): self.assertNotIn(bad,src)
        print("[PASS] Raydium CLMM adapter performs no network/filesystem/sleep")
if __name__=="__main__": unittest.main(verbosity=2)
"""
M=DEX/"raydium_clmm.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_007_raydium_clmm_hot_adapter.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-007 Raydium CLMM hot adapter installed")
print("[DEX] RAYDIUM_CLMM")
print("[BINDING] requires repo-native local CLMM quoter; no REST/Jupiter fallback")
print("[MODE] execution_authority=FALSE")
