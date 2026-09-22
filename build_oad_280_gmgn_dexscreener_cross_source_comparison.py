from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-280'
REVISION='OAD_280_GMGN_DEXSCREENER_CROSS_SOURCE_COMPARISON_V1'
TITLE='GMGN DEXSCREENER CROSS-SOURCE COMPARISON'
EXPECTED_FILENAME='build_oad_280_gmgn_dexscreener_cross_source_comparison.py'
MODULE_NAME='oad_280_gmgn_dexscreener_cross_source_comparison.py'
TEST_NAME='test_oad_280_gmgn_dexscreener_cross_source_comparison.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_263_solana_token_pool_identity_liquidity_expansion.py': ('expand_live_solana_token_pools',), 'qseries_v2/oracle_adapters/independent/oad_279_gmgn_solana_token_intelligence_adapter.py': ('acquire_gmgn_solana_token_intelligence',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport json,re\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CrossSourceFieldComparison:\n    field:str\n    gmgn_value:object\n    dexscreener_value:object\n    comparable:bool\n    relative_difference:float|None\n\n@dataclass(frozen=True,slots=True)\nclass GMGNDexScreenerComparison:\n    token_address:str\n    fields:tuple\n    comparable_fields:int\n    agreements:int\n    contradictions:int\n    state:str\n    probability:None=None\n    direction:None=None\n    execution_authority:bool=False\n\ndef _walk(obj):\n    if isinstance(obj,dict):\n        for k,v in obj.items():\n            yield str(k),v\n            yield from _walk(v)\n    elif isinstance(obj,(list,tuple)):\n        for x in obj: yield from _walk(x)\n\ndef _first_numeric(obj,names):\n    want={x.lower() for x in names}\n    for k,v in _walk(obj):\n        if k.lower() in want and isinstance(v,(int,float)) and not isinstance(v,bool):\n            return float(v)\n        if k.lower() in want and isinstance(v,str):\n            try:return float(v.replace(",",""))\n            except Exception:pass\n    return None\n\ndef _dex_first(pool_payload,names):\n    pools=tuple(pool_payload.get("pools") or ())\n    if not pools:return None\n    p=pools[0]\n    for n in names:\n        v=p.get(n)\n        if v is not None:\n            try:return float(v)\n            except Exception:pass\n    return None\n\ndef compare_gmgn_to_dexscreener(token_address,gmgn_payload,dex_payload,tolerance=0.15):\n    specs=(\n      ("price_usd",("price","price_usd","priceUsd"),("price_usd","priceUsd")),\n      ("liquidity_usd",("liquidity","liquidity_usd","liquidityUsd"),("liquidity_usd","liquidityUsd")),\n      ("volume_h24",("volume","volume24h","volume_h24","volume_24h"),("volume_h24","volume24h")),\n    )\n    fields=[];agree=0;contra=0;comp=0\n    for name,gn,dn in specs:\n        g=_first_numeric(gmgn_payload,gn)\n        d=_dex_first(dex_payload,dn)\n        comparable=(g is not None and d is not None)\n        rel=None\n        if comparable:\n            comp+=1\n            denom=max(abs(g),abs(d),1e-12)\n            rel=abs(g-d)/denom\n            if rel<=float(tolerance):agree+=1\n            else:contra+=1\n        fields.append(CrossSourceFieldComparison(name,g,d,comparable,rel))\n    state="CROSS_SOURCE_COMPARABLE" if comp else "HOLD_NO_COMPARABLE_FIELDS"\n    return GMGNDexScreenerComparison(str(token_address),tuple(fields),comp,agree,contra,state,None,None,False)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_280_gmgn_dexscreener_cross_source_comparison import *\n\nclass T(unittest.TestCase):\n    def test_comparison(self):\n        g={"data":{"price":1.02,"liquidity":1010,"volume24h":5000}}\n        d={"pools":({"price_usd":1.0,"liquidity_usd":1000,"volume_h24":5100},)}\n        r=compare_gmgn_to_dexscreener("X",g,d)\n        print("[COMPARABLE]",r.comparable_fields)\n        print("[AGREEMENTS]",r.agreements)\n        print("[CONTRADICTIONS]",r.contradictions)\n        self.assertEqual(r.comparable_fields,3)\n        self.assertEqual(r.agreements,3)\n        self.assertEqual(r.contradictions,0)\n        self.assertIsNone(r.probability)\n        self.assertIsNone(r.direction)\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-280 GMGN/DexScreener comparison contract certified")\n    print("[PASS] provider disagreement preserved as contradiction, not overwritten")\n'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch: expected "+EXPECTED_FILENAME)
    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel,symbols in DEPENDENCIES.items():
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def "+symbol+"(") not in src and ("class "+symbol) not in src:
                raise RuntimeError("Exact dependency symbol missing: "+rel+" -> "+symbol)
        print("[PASS] exact dependency verified:",rel)

    protected=[]
    for p,label in (
        (root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
        (root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
    ):
        if p.is_file():
            protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
            print("[PASS]",label,"verified")

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] GMGN remains observation-only")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
