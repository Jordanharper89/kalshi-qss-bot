from pathlib import Path
import py_compile

ROOT=Path.cwd()
DEX=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/dex"
if not (DEX/"meteora_damm_v2.py").is_file(): raise SystemExit("[FAIL] QARB-009 missing")
if not (DEX/"orca_whirlpool_live.py").is_file(): raise SystemExit("[FAIL] QARB-013 missing")

SRC=r"""
from __future__ import annotations
import struct
from dataclasses import dataclass
from time import perf_counter_ns
from .meteora_damm_v2 import PoolState,quote_exact_in

VENUE="METEORA_DAMM_V2"

@dataclass
class LivePool:
    pool:str
    token_a:str
    token_b:str
    vault_a:str
    vault_b:str
    fee_numerator:int=30
    fee_denominator:int=10000

def token_amount(raw):
    if len(raw)<72: raise RuntimeError("TOKEN_ACCOUNT_SHORT")
    return struct.unpack_from("<Q",raw,64)[0]

def hydrate(desc,account_reader):
    a,_=account_reader(desc.vault_a);b,_=account_reader(desc.vault_b)
    return PoolState(desc.pool,desc.token_a,desc.token_b,token_amount(a),token_amount(b),
                     desc.fee_numerator,desc.fee_denominator,perf_counter_ns())

def update(state,desc,address,raw,observed_ns):
    amt=token_amount(raw)
    if address==desc.vault_a: state.reserve_a=amt
    elif address==desc.vault_b: state.reserve_b=amt
    else: return False
    state.observed_ns=int(observed_ns);return True

def quote(state,input_mint,amount_in,now_ns=None):
    return quote_exact_in(state,input_mint,int(amount_in),now_ns)
"""

TEST=r"""
import struct,unittest
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.meteora_damm_v2_live import *
class T(unittest.TestCase):
    def test_hydrate_update_quote(self):
        d=LivePool("P","A","B","V","W")
        def acct(addr):
            x=bytearray(72);struct.pack_into("<Q",x,64,1000 if addr=="V" else 2000);return bytes(x),1
        s=hydrate(d,acct)
        self.assertGreater(quote(s,"A",10),0)
        x=bytearray(72);struct.pack_into("<Q",x,64,1500)
        self.assertTrue(update(s,d,"V",bytes(x),perf_counter_ns()))
        self.assertEqual(s.reserve_a,1500)
        print("[PASS] Meteora DAMM V2 warm vaults -> live update -> local quote")
if __name__=="__main__": unittest.main(verbosity=2)
"""

M=DEX/"meteora_damm_v2_live.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_014_meteora_damm_v2_live_binding.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-014 Meteora DAMM V2 live binding installed")
print("[FLOW] warm vault reserves -> accountSubscribe-ready updates -> local quote")
print("[GATE] <=750ms inherited from QARB-009")
print("[MODE] execution_authority=FALSE")
