from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-268'
REVISION='OAD_268_SOLANA_LIQUIDITY_ADD_REMOVE_CHANGE_DETECTION_V1'
TITLE='SOLANA LIQUIDITY ADD/REMOVE CHANGE DETECTION'
MODULE_NAME='oad_268_solana_liquidity_add_remove_change_detection.py'
TEST_NAME='test_oad_268_solana_liquidity_add_remove_change_detection.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py': ('SolanaHistoricalObservation',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass PoolLiquidityDelta:\n    source_id:str\n    token_address:str\n    pair_address:str\n    previous_observed_at:str\n    current_observed_at:str\n    previous_liquidity_usd:float|None\n    current_liquidity_usd:float|None\n    liquidity_change_usd:float|None\n    liquidity_change_fraction:float|None\n    state:str\n    execution_authority:bool=False\n\ndef _num(v):\n    try:\n        return float(v)\n    except (TypeError,ValueError):\n        return None\n\ndef build_pool_liquidity_deltas(records):\n    grouped={}\n    for r in tuple(records):\n        if r.observation_type!="solana_token_pool_identity_liquidity":\n            continue\n        grouped.setdefault(r.source_id,[]).append(r)\n\n    out=[]\n    for source_id,rows in grouped.items():\n        rows=sorted(rows,key=lambda x:(-1 if x.sequence_number is None else int(x.sequence_number),x.observed_at,x.observation_id))\n        if len(rows)<2:\n            continue\n        a,b=rows[-2],rows[-1]\n        pa={str(x.get("pair_address")):x for x in tuple(a.payload.get("pools") or ()) if x.get("pair_address")}\n        pb={str(x.get("pair_address")):x for x in tuple(b.payload.get("pools") or ()) if x.get("pair_address")}\n        for pair in sorted(set(pa)&set(pb)):\n            av=_num(pa[pair].get("liquidity_usd")); bv=_num(pb[pair].get("liquidity_usd"))\n            delta=None if av is None or bv is None else bv-av\n            frac=None if delta is None or not av else delta/av\n            state="UNKNOWN" if delta is None else ("LIQUIDITY_ADDED" if delta>0 else "LIQUIDITY_REMOVED" if delta<0 else "UNCHANGED")\n            out.append(PoolLiquidityDelta(\n                source_id,\n                str(b.payload.get("token_address") or ""),\n                pair,\n                a.observed_at,b.observed_at,\n                av,bv,delta,frac,state,False,\n            ))\n    return tuple(out)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation\nfrom qseries_v2.oracle_adapters.independent.oad_268_solana_liquidity_add_remove_change_detection import *\n\nclass T(unittest.TestCase):\n    def test_delta(self):\n        a=SolanaHistoricalObservation("a","source.dex.solana.token_pools.X","solana_token_pool_identity_liquidity","2026-09-01T00:00:00+00:00",1,"dexscreener","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100.0},)})\n        b=SolanaHistoricalObservation("b","source.dex.solana.token_pools.X","solana_token_pool_identity_liquidity","2026-09-01T00:01:00+00:00",2,"dexscreener","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":125.0},)})\n        r=build_pool_liquidity_deltas((a,b))\n        print("[DELTA]",r[0].liquidity_change_usd,r[0].state)\n        self.assertEqual(r[0].liquidity_change_usd,25.0)\n        self.assertEqual(r[0].state,"LIQUIDITY_ADDED")\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-268 deterministic liquidity add/remove change detection certified")\n'

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
        if exp not in lines:
            lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
