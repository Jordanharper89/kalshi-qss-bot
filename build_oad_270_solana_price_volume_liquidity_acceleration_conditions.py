from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-270'
REVISION='OAD_270_SOLANA_PRICE_VOLUME_LIQUIDITY_ACCELERATION_CONDITIONS_V1'
TITLE='SOLANA PRICE/VOLUME/LIQUIDITY ACCELERATION CONDITIONS'
MODULE_NAME='oad_270_solana_price_volume_liquidity_acceleration_conditions.py'
TEST_NAME='test_oad_270_solana_price_volume_liquidity_acceleration_conditions.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_268_solana_liquidity_add_remove_change_detection.py': ('build_pool_liquidity_deltas',), 'qseries_v2/oracle_adapters/independent/oad_269_solana_buy_sell_volume_pressure_history.py': ('build_pool_pressure_history',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_268_solana_liquidity_add_remove_change_detection import build_pool_liquidity_deltas\nfrom .oad_269_solana_buy_sell_volume_pressure_history import build_pool_pressure_history\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass SolanaAccelerationCondition:\n    source_id:str\n    pair_address:str\n    observed_at:str\n    conditions:tuple\n    evidence_count:int\n    state:str\n    probability:None=None\n    direction:None=None\n    execution_authority:bool=False\n\ndef _sign(v,pos,neg,zero="FLAT",unknown="UNKNOWN"):\n    if v is None:return unknown\n    if v>0:return pos\n    if v<0:return neg\n    return zero\n\ndef build_solana_acceleration_conditions(records):\n    liq={(x.source_id,x.pair_address):x for x in build_pool_liquidity_deltas(records)}\n    pressure={(x.source_id,x.pair_address):x for x in build_pool_pressure_history(records)}\n    out=[]\n    for key in sorted(set(liq)&set(pressure)):\n        l=liq[key]; p=pressure[key]\n        conditions=(\n            ("liquidity",_sign(l.liquidity_change_usd,"RISING","FALLING")),\n            ("volume",_sign(p.volume_change,"RISING","FALLING")),\n            ("price",_sign(p.price_change_fraction,"RISING","FALLING")),\n            ("order_flow",p.state),\n        )\n        known=sum(1 for _,v in conditions if v!="UNKNOWN")\n        state="COMPOSITE_READY" if known>=3 else "PARTIAL"\n        out.append(SolanaAccelerationCondition(l.source_id,l.pair_address,p.current_observed_at,conditions,known,state,None,None,False))\n    return tuple(out)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation\nfrom qseries_v2.oracle_adapters.independent.oad_270_solana_price_volume_liquidity_acceleration_conditions import *\n\nclass T(unittest.TestCase):\n    def test_conditions(self):\n        a=SolanaHistoricalObservation("a","S","solana_token_pool_identity_liquidity","t1",1,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100,"buys_h24":10,"sells_h24":9,"volume_h24":100,"price_usd":1.0},)})\n        b=SolanaHistoricalObservation("b","S","solana_token_pool_identity_liquidity","t2",2,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":125,"buys_h24":15,"sells_h24":10,"volume_h24":130,"price_usd":1.1},)})\n        r=build_solana_acceleration_conditions((a,b))[0]\n        print("[CONDITIONS]",r.conditions)\n        print("[STATE]",r.state)\n        self.assertEqual(r.state,"COMPOSITE_READY")\n        self.assertIsNone(r.probability)\n        self.assertIsNone(r.direction)\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-270 factual acceleration-condition formation certified")\n    print("[PASS] no probability or direction inferred")\n'

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
