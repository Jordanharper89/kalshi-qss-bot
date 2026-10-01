from pathlib import Path
import py_compile
ROOT=Path.cwd()
DEX=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/dex"
if not (DEX/"raydium_clmm.py").is_file(): raise SystemExit("[FAIL] QARB-007 missing")
SRC=r"""
from dataclasses import dataclass
from time import perf_counter_ns

VENUE="ORCA_WHIRLPOOL"
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
    if not state.fresh(now_ns): raise RuntimeError("STALE_ORCA_WHIRLPOOL")
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
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.orca_whirlpool import *
class T(unittest.TestCase):
    def test_local_quoter_bridge(self):
        s=bind_local_quoter("P","SOL","T",lambda mint,x:x+9)
        self.assertEqual(quote_exact_in(s,"T",11),20)
        print("[PASS] Orca Whirlpool repo-native local quoter bridge")
    def test_stale(self):
        s=bind_local_quoter("P","SOL","T",lambda m,x:x,perf_counter_ns()-800_000_000)
        with self.assertRaisesRegex(RuntimeError,"STALE"): quote_exact_in(s,"SOL",1)
        print("[PASS] Orca >750ms state rejected")
    def test_no_adapter_io(self):
        src=inspect.getsource(quote_exact_in).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"): self.assertNotIn(bad,src)
        print("[PASS] Orca adapter performs no network/filesystem/sleep")
if __name__=="__main__": unittest.main(verbosity=2)
"""
M=DEX/"orca_whirlpool.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_008_orca_whirlpool_hot_adapter.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-008 Orca Whirlpool hot adapter installed")
print("[DEX] ORCA_WHIRLPOOL")
print("[BINDING] requires repo-native local Whirlpool quoter; no REST/Jupiter fallback")
print("[MODE] execution_authority=FALSE")
