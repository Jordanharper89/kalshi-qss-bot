from pathlib import Path
import py_compile
ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
if not (SUB/"multidex_live_hunter.py").is_file(): raise SystemExit("[FAIL] QARB-015 missing")
SRC=r"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

TARGETS={"RAYDIUM_CPMM","RAYDIUM_CLMM","ORCA","ORCA_WHIRLPOOL","METEORA_DAMM","METEORA_DAMM_V2"}
CERTIFIED_NAMES=(
 "raydium_exact_instruction_pool_role_decoder.json",
 "raydium_exact_pair_orientation_decoder.json",
 "meteora_orca_source_certified_role_decoder.json",
 "meteora_orca_exact_transfer_reconciler.json",
)

@dataclass(frozen=True)
class RoleRow:
    venue:str
    pool:str
    token_a:str|None
    token_b:str|None
    accounts:tuple
    source:str

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from _walk(v)
    elif isinstance(x,list):
        for v in x: yield from _walk(v)

def _pick(d,*names):
    for n in names:
        v=d.get(n)
        if isinstance(v,str) and len(v)>=20: return v
    return None

def _accounts(d):
    z=[]
    def add(v):
        if isinstance(v,str) and len(v)>=20 and v not in z: z.append(v)
        elif isinstance(v,(list,tuple)):
            for q in v: add(q)
        elif isinstance(v,dict):
            for q in v.values(): add(q)
    for k,v in d.items():
        kl=k.lower()
        if any(t in kl for t in ("vault","tick","array","observation","bitmap","pool_state","token_account")):
            add(v)
    add(d.get("accounts"))
    return tuple(z)

def load(root):
    root=Path(root);rows=[];seen=set()
    files=[]
    state=root/"runtime_state"
    if state.exists():
        for p in state.rglob("*.json"):
            if p.name in CERTIFIED_NAMES or any(x in p.name for x in ("raydium_exact","meteora_orca")):
                files.append(p)
    for p in files:
        try: obj=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        for d in _walk(obj):
            venue=str(d.get("venue") or d.get("venue_name") or d.get("family") or "").upper()
            if venue not in TARGETS: continue
            pool=_pick(d,"pool","pool_id","pool_address","market_address")
            if not pool: continue
            ta=_pick(d,"token_a","mint_a","token_0","mint_0","base_mint","input_mint")
            tb=_pick(d,"token_b","mint_b","token_1","mint_1","quote_mint","output_mint")
            acc=_accounts(d)
            key=(venue,pool,acc)
            if key in seen: continue
            seen.add(key)
            rows.append(RoleRow(venue,pool,ta,tb,acc,str(p.relative_to(root))))
    return rows

def summary(rows):
    out={}
    for r in rows: out[r.venue]=out.get(r.venue,0)+1
    return out
"""
TEST=r"""
import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.certified_roles import *
class T(unittest.TestCase):
    def test_certified_role_load(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runtime_state/x";p.mkdir(parents=True)
            (p/"raydium_exact_instruction_pool_role_decoder.json").write_text(json.dumps({
              "rows":[{"venue":"RAYDIUM_CLMM","pool":"P"*32,"mint_a":"A"*32,"mint_b":"B"*32,
                       "accounts":{"vault_a":"V"*32,"vault_b":"W"*32,"tick_array":"T"*32}}]}),encoding="utf-8")
            rows=load(td);self.assertEqual(len(rows),1);self.assertEqual(len(rows[0].accounts),3)
        print("[PASS] certified role artifacts -> exact watched-account manifest")
if __name__=="__main__": unittest.main(verbosity=2)
"""
M=SUB/"certified_roles.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_016_certified_multidex_role_manifest.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-016 certified multi-DEX role manifest installed")
print("[SOURCE] existing Raydium exact-role + Meteora/Orca source-certified artifacts only")
print("[MODE] execution_authority=FALSE")
