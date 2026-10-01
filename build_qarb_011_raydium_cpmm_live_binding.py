from pathlib import Path
import py_compile

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
DEX=SUB/"dex"
if not (DEX/"raydium_cpmm.py").is_file():
    raise SystemExit("[FAIL] QARB-006 missing")
if not (SUB/"live_account_stream.py").is_file():
    raise SystemExit("[FAIL] QARB-005 missing")

SRC=r"""
from __future__ import annotations
import json,struct
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from .raydium_cpmm import PoolState,quote_exact_in

VENUE="RAYDIUM_CPMM"

@dataclass
class LivePool:
    pool:str
    token_a:str
    token_b:str
    vault_a:str
    vault_b:str
    fee_numerator:int=25
    fee_denominator:int=10000

def token_amount(raw):
    if len(raw)<72: raise RuntimeError("TOKEN_ACCOUNT_SHORT")
    return struct.unpack_from("<Q",raw,64)[0]

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from _walk(v)
    elif isinstance(x,list):
        for v in x:
            yield from _walk(v)

def _pick(d,*names):
    for n in names:
        v=d.get(n)
        if isinstance(v,str) and len(v)>=20:
            return v
    return None

def discover(root):
    root=Path(root)
    found={}
    candidates=list((root/"runtime_state").rglob("*.json")) if (root/"runtime_state").exists() else []
    for p in candidates:
        try: obj=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        for d in _walk(obj):
            venue=str(d.get("venue") or d.get("venue_name") or d.get("family") or "").upper()
            if "RAYDIUM_CPMM" not in venue and venue!="CPMM": continue
            pool=_pick(d,"pool","pool_id","pool_address","amm_config_pool")
            ta=_pick(d,"token_a","mint_a","token_0","mint_0","base_mint")
            tb=_pick(d,"token_b","mint_b","token_1","mint_1","quote_mint")
            va=_pick(d,"vault_a","token_vault_a","vault_0","base_vault")
            vb=_pick(d,"vault_b","token_vault_b","vault_1","quote_vault")
            acc=d.get("accounts")
            if isinstance(acc,dict):
                va=va or _pick(acc,"vault_a","token_vault_a","vault_0","base_vault")
                vb=vb or _pick(acc,"vault_b","token_vault_b","vault_1","quote_vault")
            if all((pool,ta,tb,va,vb)):
                found[pool]=LivePool(pool,ta,tb,va,vb,
                    int(d.get("fee_numerator") or 25),int(d.get("fee_denominator") or 10000))
    return list(found.values())

def hydrate(desc,account_reader):
    a,_=account_reader(desc.vault_a)
    b,_=account_reader(desc.vault_b)
    return PoolState(desc.pool,desc.token_a,desc.token_b,token_amount(a),token_amount(b),
                     desc.fee_numerator,desc.fee_denominator,perf_counter_ns())

def update(state,desc,address,raw,observed_ns):
    amt=token_amount(raw)
    if address==desc.vault_a:
        state.reserve_a=amt
    elif address==desc.vault_b:
        state.reserve_b=amt
    else:
        return False
    state.observed_ns=int(observed_ns)
    return True

def quote(state,input_mint,amount_in,now_ns=None):
    return quote_exact_in(state,input_mint,amount_in,now_ns)
"""

TEST=r"""
import json,struct,tempfile,unittest
from pathlib import Path
from time import perf_counter_ns
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.dex.raydium_cpmm_live import *

class T(unittest.TestCase):
    def test_registry_discovery_and_live_update(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runtime_state/x";p.mkdir(parents=True)
            obj={"rows":[{"venue":"RAYDIUM_CPMM","pool":"P"*32,"mint_a":"A"*32,"mint_b":"B"*32,
                          "vault_a":"V"*32,"vault_b":"W"*32}]}
            (p/"x.json").write_text(json.dumps(obj),encoding="utf-8")
            rows=discover(td);self.assertEqual(len(rows),1)
            def acct(addr):
                raw=bytearray(72);struct.pack_into("<Q",raw,64,1000 if addr=="V"*32 else 2000)
                return bytes(raw),1
            st=hydrate(rows[0],acct)
            raw=bytearray(72);struct.pack_into("<Q",raw,64,1500)
            self.assertTrue(update(st,rows[0],"V"*32,bytes(raw),perf_counter_ns()))
            self.assertEqual(st.reserve_a,1500)
        print("[PASS] Raydium CPMM artifact discovery -> hydrate -> live reserve update")
    def test_local_quote(self):
        d=LivePool("P","A","B","V","W");s=PoolState("P","A","B",1000,2000,25,10000,perf_counter_ns())
        self.assertGreater(quote(s,"A",10),0)
        print("[PASS] Raydium CPMM live state feeds local quote")
if __name__=="__main__": unittest.main(verbosity=2)
"""

M=DEX/"raydium_cpmm_live.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_011_raydium_cpmm_live_binding.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-011 Raydium CPMM live binding installed")
print("[FLOW] existing artifact roles -> warm vaults -> accountSubscribe-ready reserve updates -> local quote")
print("[GATE] <=750ms inherited from QARB-006")
print("[MODE] execution_authority=FALSE")
