from pathlib import Path
import py_compile

ROOT=Path.cwd()
DEX=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/dex"
if not (DEX/"orca_whirlpool.py").is_file(): raise SystemExit("[FAIL] QARB-008 missing")
if not (DEX/"raydium_clmm_live.py").is_file(): raise SystemExit("[FAIL] QARB-012 missing")

SRC=r"""
from __future__ import annotations
import importlib,os
from dataclasses import dataclass
from time import perf_counter_ns
from .orca_whirlpool import bind_local_quoter,quote_exact_in

VENUE="ORCA_WHIRLPOOL"
PROVIDER_ENV="QARB_ORCA_WHIRLPOOL_PROVIDER"

@dataclass
class LivePool:
    pool:str
    token_a:str
    token_b:str
    watched_accounts:tuple
    state:object=None
    observed_ns:int=0

def load_provider(spec=None):
    spec=(spec or os.getenv(PROVIDER_ENV,"")).strip()
    if not spec: raise RuntimeError("ORCA_LOCAL_PROVIDER_NOT_BOUND")
    if ":" not in spec: raise RuntimeError("BAD_PROVIDER_SPEC")
    mod,name=spec.split(":",1);fn=getattr(importlib.import_module(mod),name)
    if not callable(fn): raise RuntimeError("PROVIDER_NOT_CALLABLE")
    return fn

def bind(desc,provider=None,observed_ns=None):
    fn=provider or load_provider()
    def q(input_mint,amount_in): return int(fn(desc,input_mint,int(amount_in)))
    desc.state=bind_local_quoter(desc.pool,desc.token_a,desc.token_b,q,
        perf_counter_ns() if observed_ns is None else int(observed_ns))
    return desc

def touch(desc,address,raw,observed_ns,provider_update=None):
    if address not in desc.watched_accounts: return False
    if provider_update is not None: provider_update(desc,address,raw)
    if desc.state is None: raise RuntimeError("ORCA_LOCAL_PROVIDER_NOT_BOUND")
    desc.state.observed_ns=int(observed_ns);return True

def quote(desc,input_mint,amount_in,now_ns=None):
    if desc.state is None: raise RuntimeError("ORCA_LOCAL_PROVIDER_NOT_BOUND")
    return quote_exact_in(desc.state,input_mint,int(amount_in),now_ns)
"""

TEST=r"""
import unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.orca_whirlpool_live import *
class T(unittest.TestCase):
    def test_fail_closed(self):
        d=LivePool("P","A","B",("X",))
        with self.assertRaisesRegex(RuntimeError,"NOT_BOUND"): quote(d,"A",1)
        print("[PASS] Orca refuses fake pricing without native local provider")
    def test_provider_binding(self):
        d=LivePool("P","A","B",("X",))
        bind(d,provider=lambda desc,mint,x:x+5)
        self.assertTrue(touch(d,"X",b"x",perf_counter_ns()))
        self.assertEqual(quote(d,"B",8),13)
        print("[PASS] Orca live account touch -> bound local quote provider")
if __name__=="__main__": unittest.main(verbosity=2)
"""

M=DEX/"orca_whirlpool_live.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_013_orca_whirlpool_live_binding.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-013 Orca Whirlpool live-binding contract installed")
print("[FAIL_CLOSED] no REST/Jupiter/fake Whirlpool pricing")
print("[MODE] execution_authority=FALSE")
