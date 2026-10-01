from pathlib import Path
import py_compile,importlib

ROOT=Path.cwd()
DEX=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/dex"
if not (DEX/"raydium_clmm.py").is_file(): raise SystemExit("[FAIL] QARB-007 missing")
if not (DEX/"raydium_cpmm_live.py").is_file(): raise SystemExit("[FAIL] QARB-011 missing")

SRC=r"""
from __future__ import annotations
import importlib,os
from dataclasses import dataclass
from time import perf_counter_ns
from .raydium_clmm import bind_local_quoter,quote_exact_in

VENUE="RAYDIUM_CLMM"
PROVIDER_ENV="QARB_RAYDIUM_CLMM_PROVIDER"

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
    if not spec:
        raise RuntimeError("RAYDIUM_CLMM_LOCAL_PROVIDER_NOT_BOUND")
    if ":" not in spec:
        raise RuntimeError("BAD_PROVIDER_SPEC")
    mod,name=spec.split(":",1)
    fn=getattr(importlib.import_module(mod),name)
    if not callable(fn): raise RuntimeError("PROVIDER_NOT_CALLABLE")
    return fn

def bind(desc,provider=None,observed_ns=None):
    fn=provider or load_provider()
    def q(input_mint,amount_in):
        return int(fn(desc,input_mint,int(amount_in)))
    desc.state=bind_local_quoter(desc.pool,desc.token_a,desc.token_b,q,
        perf_counter_ns() if observed_ns is None else int(observed_ns))
    return desc

def touch(desc,address,raw,observed_ns,provider_update=None):
    if address not in desc.watched_accounts: return False
    if provider_update is not None:
        provider_update(desc,address,raw)
    if desc.state is None: raise RuntimeError("RAYDIUM_CLMM_LOCAL_PROVIDER_NOT_BOUND")
    desc.state.observed_ns=int(observed_ns)
    return True

def quote(desc,input_mint,amount_in,now_ns=None):
    if desc.state is None: raise RuntimeError("RAYDIUM_CLMM_LOCAL_PROVIDER_NOT_BOUND")
    return quote_exact_in(desc.state,input_mint,int(amount_in),now_ns)
"""

TEST=r"""
import unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.raydium_clmm_live import *
class T(unittest.TestCase):
    def test_fail_closed_without_provider(self):
        d=LivePool("P","A","B",("X",))
        with self.assertRaisesRegex(RuntimeError,"NOT_BOUND"): quote(d,"A",1)
        print("[PASS] Raydium CLMM refuses fake pricing when no native local provider bound")
    def test_provider_binding_and_touch(self):
        d=LivePool("P","A","B",("X","Y"))
        bind(d,provider=lambda desc,mint,x:x*3)
        self.assertTrue(touch(d,"X",b"abc",perf_counter_ns()))
        self.assertEqual(quote(d,"A",7),21)
        print("[PASS] Raydium CLMM live account touch -> bound local quote provider")
if __name__=="__main__": unittest.main(verbosity=2)
"""

M=DEX/"raydium_clmm_live.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_012_raydium_clmm_live_binding.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-012 Raydium CLMM live-binding contract installed")
print("[FAIL_CLOSED] no REST/Jupiter/fake CLMM math if repo-native local provider is not bound")
print("[HOT] live account touches refresh provider-backed local state")
print("[MODE] execution_authority=FALSE")
