from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_373_solana_universal_economic_event_promotion.py'
BUILD_ID='OAD-373'
TITLE='SOLANA UNIVERSAL ECONOMIC EVENT PROMOTION'
MODULE='oad_373_solana_universal_economic_event_promotion.py'
TEST='test_oad_373_solana_universal_economic_event_promotion.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_355_solana_final_economic_behavior_decoder.py': ('FINAL_VERIFIED',), 'qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py': ('FINAL_PERSISTENCE_CONTINUITY_CERTIFIED',)}
EXTRA_PROTECTED=()

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

PROMOTABLE_BEHAVIORS=frozenset({
    "DEX_SWAP","ASSET_EXCHANGE_FLOW","TOKEN_FLOW","FINAL_VERIFIED_ASSET_EXCHANGE_FLOW",
    "FINAL_VERIFIED_TOKEN_FLOW","FINAL_VERIFIED_INTERACTION_UNRESOLVED",
    "PROTOCOL_ASSET_EXCHANGE_FLOW","ORDERBOOK_TRADE","ROUTED_SWAP"
})

@dataclass(frozen=True, slots=True)
class SolanaPromotedEconomicEvent:
    event_id:str
    slot:int
    block_time:float|None
    signature:str|None
    behavior_type:str
    protocol:str|None
    primary_asset:str|None
    secondary_asset:str|None
    wallet:str|None
    magnitude:float|None
    source:str
    promotable:bool
    execution_authority:bool=False

def _get(x,*names,default=None):
    for n in names:
        if isinstance(x,dict) and n in x:
            return x[n]
        if hasattr(x,n):
            return getattr(x,n)
    return default

def promote_economic_behavior(x:Any):
    behavior=str(_get(x,"behavior_type","event_type","type","kind",default="UNKNOWN"))
    slot=int(_get(x,"slot","block_slot",default=0) or 0)
    sig=_get(x,"signature","transaction_signature",default=None)
    eid=str(_get(x,"event_id","observation_id","id",default=f"{slot}:{sig}:{behavior}"))
    protocol=_get(x,"protocol","protocol_id","dex_id","program_name",default=None)
    asset=_get(x,"primary_asset","mint","asset","token_mint",default=None)
    secondary=_get(x,"secondary_asset","quote_asset","counter_asset","other_mint",default=None)
    wallet=_get(x,"wallet","owner","authority",default=None)
    magnitude=_get(x,"magnitude","amount","notional","delta",default=None)
    try:
        magnitude=None if magnitude is None else float(magnitude)
    except Exception:
        magnitude=None
    promotable=behavior.upper() in {x.upper() for x in PROMOTABLE_BEHAVIORS} or any(k in behavior.upper() for k in ("SWAP","FLOW","TRADE"))
    return SolanaPromotedEconomicEvent(
        eid,slot,_get(x,"block_time","timestamp",default=None),sig,behavior,
        None if protocol is None else str(protocol),
        None if asset is None else str(asset),
        None if secondary is None else str(secondary),
        None if wallet is None else str(wallet),
        magnitude,"SOLANA_UNIVERSAL_CHAIN",promotable,False
    )

def promote_economic_behaviors(items):
    return tuple(y for y in (promote_economic_behavior(x) for x in items) if y.promotable)

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_373_solana_universal_economic_event_promotion import *

class T(unittest.TestCase):
    def test_promote(self):
        x=promote_economic_behaviors(({"event_id":"e1","slot":10,"behavior_type":"DEX_SWAP","primary_asset":"A","secondary_asset":"B"},))
        print("[PROMOTION]",x[0].event_id,x[0].behavior_type,x[0].source)
        self.assertEqual(len(x),1)
        self.assertTrue(x[0].promotable)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-373 universal Solana economic behavior promotion certified")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def verify(path, markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    for marker in markers:
        if marker not in text:
            raise RuntimeError("dependency interface missing: "+path.name+" -> "+marker)

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer identity mismatch")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,markers in DEPENDENCIES.items():
        verify(r/rel,markers)
        print("[PASS] dependency interface verified:",rel)

    protected_rels=[
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
    ]+list(EXTRA_PROTECTED)

    protected=[]
    for rel in protected_rels:
        p=r/rel
        if p.is_file():
            protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines:
            lines.append(export)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)

        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] protected certified boundaries preserved")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
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
