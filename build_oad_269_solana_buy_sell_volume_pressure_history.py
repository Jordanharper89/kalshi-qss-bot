from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-269'
REVISION='OAD_269_SOLANA_BUY_SELL_VOLUME_PRESSURE_HISTORY_V1'
TITLE='SOLANA BUY/SELL + VOLUME PRESSURE HISTORY'
MODULE_NAME='oad_269_solana_buy_sell_volume_pressure_history.py'
TEST_NAME='test_oad_269_solana_buy_sell_volume_pressure_history.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py': ('SolanaHistoricalObservation',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass PoolPressureDelta:\n    source_id:str\n    pair_address:str\n    previous_observed_at:str\n    current_observed_at:str\n    buys_h24:int|None\n    sells_h24:int|None\n    buy_sell_imbalance:int|None\n    volume_h24:float|None\n    volume_change:float|None\n    price_usd:float|None\n    price_change_fraction:float|None\n    state:str\n    execution_authority:bool=False\n\ndef _num(v):\n    try:return float(v)\n    except (TypeError,ValueError):return None\n\ndef _int(v):\n    try:return int(v)\n    except (TypeError,ValueError):return None\n\ndef build_pool_pressure_history(records):\n    grouped={}\n    for r in tuple(records):\n        if r.observation_type=="solana_token_pool_identity_liquidity":\n            grouped.setdefault(r.source_id,[]).append(r)\n    out=[]\n    for source_id,rows in grouped.items():\n        rows=sorted(rows,key=lambda x:(-1 if x.sequence_number is None else int(x.sequence_number),x.observed_at,x.observation_id))\n        if len(rows)<2: continue\n        a,b=rows[-2],rows[-1]\n        pa={str(x.get("pair_address")):x for x in tuple(a.payload.get("pools") or ()) if x.get("pair_address")}\n        pb={str(x.get("pair_address")):x for x in tuple(b.payload.get("pools") or ()) if x.get("pair_address")}\n        for pair in sorted(set(pa)&set(pb)):\n            old,new=pa[pair],pb[pair]\n            buys=_int(new.get("buys_h24")); sells=_int(new.get("sells_h24"))\n            imbalance=None if buys is None or sells is None else buys-sells\n            vold=_num(old.get("volume_h24")); vnew=_num(new.get("volume_h24"))\n            vdelta=None if vold is None or vnew is None else vnew-vold\n            pold=_num(old.get("price_usd")); pnew=_num(new.get("price_usd"))\n            pfrac=None if pold is None or pnew is None or not pold else (pnew-pold)/pold\n            if imbalance is None: state="UNKNOWN"\n            elif imbalance>0: state="BUY_PRESSURE"\n            elif imbalance<0: state="SELL_PRESSURE"\n            else: state="BALANCED"\n            out.append(PoolPressureDelta(source_id,pair,a.observed_at,b.observed_at,buys,sells,imbalance,vnew,vdelta,pnew,pfrac,state,False))\n    return tuple(out)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation\nfrom qseries_v2.oracle_adapters.independent.oad_269_solana_buy_sell_volume_pressure_history import *\n\nclass T(unittest.TestCase):\n    def test_pressure(self):\n        a=SolanaHistoricalObservation("a","S","solana_token_pool_identity_liquidity","t1",1,"dex","X",{"pools":({"pair_address":"P","buys_h24":10,"sells_h24":9,"volume_h24":100,"price_usd":1.0},)})\n        b=SolanaHistoricalObservation("b","S","solana_token_pool_identity_liquidity","t2",2,"dex","X",{"pools":({"pair_address":"P","buys_h24":15,"sells_h24":10,"volume_h24":130,"price_usd":1.1},)})\n        r=build_pool_pressure_history((a,b))[0]\n        print("[PRESSURE]",r.buy_sell_imbalance,r.volume_change,r.price_change_fraction,r.state)\n        self.assertEqual(r.buy_sell_imbalance,5)\n        self.assertEqual(r.volume_change,30.0)\n        self.assertEqual(r.state,"BUY_PRESSURE")\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-269 buy/sell + volume-pressure history certified")\n'

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
