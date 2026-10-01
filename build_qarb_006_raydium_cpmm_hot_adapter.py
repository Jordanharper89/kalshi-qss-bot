from pathlib import Path
import py_compile
ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
if not (SUB/"live_account_stream.py").is_file():
    raise SystemExit("[FAIL] QARB-005 missing")
DEX=SUB/"dex"
DEX.mkdir(parents=True,exist_ok=True)
(DEX/"__init__.py").write_text("",encoding="utf-8")
SRC=r"""
from dataclasses import dataclass
from time import perf_counter_ns

VENUE="RAYDIUM_CPMM"
MAX_AGE_MS=750.0

@dataclass
class PoolState:
    pool:str
    token_a:str
    token_b:str
    reserve_a:int
    reserve_b:int
    fee_numerator:int
    fee_denominator:int
    observed_ns:int

    def fresh(self,now_ns=None,max_age_ms=MAX_AGE_MS):
        now=perf_counter_ns() if now_ns is None else int(now_ns)
        return (now-self.observed_ns)/1e6 <= float(max_age_ms)

def quote_exact_in(state,input_mint,amount_in,now_ns=None):
    if not state.fresh(now_ns):
        raise RuntimeError("STALE_RAYDIUM_CPMM")
    x=int(amount_in)
    if x<=0: raise RuntimeError("BAD_AMOUNT")
    if state.fee_denominator<=0 or state.fee_numerator<0 or state.fee_numerator>=state.fee_denominator:
        raise RuntimeError("BAD_FEE")
    net=x*(state.fee_denominator-state.fee_numerator)//state.fee_denominator
    if input_mint==state.token_a:
        rin,rout=state.reserve_a,state.reserve_b
    elif input_mint==state.token_b:
        rin,rout=state.reserve_b,state.reserve_a
    else:
        raise RuntimeError("MINT_NOT_IN_POOL")
    if rin<=0 or rout<=0: raise RuntimeError("EMPTY_POOL")
    return rout*net//(rin+net)

def update_reserve(state,mint,new_amount,observed_ns):
    if mint==state.token_a: state.reserve_a=int(new_amount)
    elif mint==state.token_b: state.reserve_b=int(new_amount)
    else: raise RuntimeError("MINT_NOT_IN_POOL")
    state.observed_ns=int(observed_ns)
    return state
"""
TEST=r"""
import inspect,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.raydium_cpmm import *
class T(unittest.TestCase):
    def test_bidirectional_local_quote(self):
        s=PoolState("P","SOL","T",1_000_000_000,2_000_000_000,25,10000,perf_counter_ns())
        self.assertGreater(quote_exact_in(s,"SOL",10_000_000),0)
        self.assertGreater(quote_exact_in(s,"T",10_000_000),0)
        print("[PASS] Raydium CPMM exact-in local math both directions")
    def test_stale_rejected(self):
        s=PoolState("P","SOL","T",1,2,25,10000,perf_counter_ns()-800_000_000)
        with self.assertRaisesRegex(RuntimeError,"STALE"): quote_exact_in(s,"SOL",1)
        print("[PASS] Raydium CPMM >750ms state rejected")
    def test_no_hot_io(self):
        src=(inspect.getsource(quote_exact_in)+inspect.getsource(update_reserve)).lower()
        for bad in ("rpc(","requests","urllib","open(","sleep(","subprocess"): self.assertNotIn(bad,src)
        print("[PASS] Raydium CPMM hot quote/update has no network/filesystem/sleep")
if __name__=="__main__": unittest.main(verbosity=2)
"""
MOD=DEX/"raydium_cpmm.py";MOD.write_text(SRC,encoding="utf-8");py_compile.compile(str(MOD),doraise=True)
T=ROOT/"test_qarb_006_raydium_cpmm_hot_adapter.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-006 Raydium CPMM hot adapter installed")
print("[DEX] RAYDIUM_CPMM")
print("[HOT] local integer quote math; bidirectional; <=750ms freshness")
print("[MODE] execution_authority=FALSE")
