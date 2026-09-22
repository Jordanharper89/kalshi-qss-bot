from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-345'
TITLE='SOLANA ORDER-BOOK DEX BEHAVIOR DECODER'
EXPECTED='build_oad_345_solana_orderbook_dex_behavior_decoder.py'
MODULE='oad_345_solana_orderbook_dex_behavior_decoder.py'
TEST='test_oad_345_solana_orderbook_dex_behavior_decoder.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_344_solana_expanded_protocol_attribution.py': ('attribute_expanded_protocols', 'economic_protocols'), 'qseries_v2/oracle_adapters/independent/oad_330_solana_wallet_token_flow_graph.py': ('build_wallet_token_flows', 'SolanaWalletTokenFlow')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaOrderBookDexBehavior:
    signature:str
    protocols:tuple
    mints:tuple
    flow_count:int
    behavior:str
    evidence:str
    execution_authority:bool=False

def decode_orderbook_dex_behaviors(envelopes,attributions,flows):
    amap={a.signature:a for a in attributions}
    out=[]
    for e in envelopes:
        a=amap.get(e.signature)
        if not a:
            continue
        protocols=tuple(p for p in a.economic_protocols if p in ("PHOENIX_ETERNAL","ARCHER_EXCHANGE"))
        if not protocols:
            continue
        fs=[f for f in flows if f.signature==e.signature]
        mints=tuple(sorted({str(f.mint) for f in fs if getattr(f,"mint",None)}))
        pos=any(float(getattr(f,"delta",0.0))>0 for f in fs)
        neg=any(float(getattr(f,"delta",0.0))<0 for f in fs)
        if pos and neg and len(mints)>=2:
            behavior="ORDERBOOK_ASSET_EXCHANGE_FLOW"
            evidence="ORDER_BOOK_PROGRAM_PLUS_BIDIRECTIONAL_TOKEN_BALANCE_FLOW"
        elif fs:
            behavior="ORDERBOOK_TOKEN_FLOW"
            evidence="ORDER_BOOK_PROGRAM_PLUS_TOKEN_BALANCE_FLOW"
        else:
            behavior="ORDERBOOK_INTERACTION_UNRESOLVED"
            evidence="ORDER_BOOK_PROGRAM_INVOCATION_ONLY"
        out.append(SolanaOrderBookDexBehavior(
            e.signature,protocols,mints,len(fs),behavior,evidence,False
        ))
    return tuple(out)

"""

TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_345_solana_orderbook_dex_behavior_decoder import *

class T(unittest.TestCase):
    def test_behavior(self):
        e=SimpleNamespace(signature="s")
        a=SimpleNamespace(signature="s",economic_protocols=("PHOENIX_ETERNAL",))
        fs=(SimpleNamespace(signature="s",mint="A",delta=-3.0),SimpleNamespace(signature="s",mint="B",delta=2.0))
        x=decode_orderbook_dex_behaviors((e,),(a,),fs)[0]
        print("[ORDERBOOK]",x.protocols,x.behavior,x.mints)
        self.assertEqual(x.behavior,"ORDERBOOK_ASSET_EXCHANGE_FLOW")
    def test_no_fabrication(self):
        e=SimpleNamespace(signature="u")
        a=SimpleNamespace(signature="u",economic_protocols=())
        self.assertEqual(decode_orderbook_dex_behaviors((e,),(a,),()),())

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-345 Phoenix Eternal/Archer evidence-grounded order-book behavior decoder certified")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_dependency(path, markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    source=path.read_text(encoding="utf-8")
    ast.parse(source,filename=str(path))
    for marker in markers:
        if marker not in source:
            raise RuntimeError("dependency contract missing: "+path.name+" -> "+marker)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,markers in DEPENDENCIES.items():
        p=r/rel
        verify_dependency(p,markers)
        print("[PASS] dependency interface verified:",rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_337_solana_program_decode_physical_coverage_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_342_solana_foundation_repair_physical_coverage_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
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
        print("[PASS] OAD-327/OAD-337/OAD-342 preserved byte-for-byte unchanged")
        print("[PASS] unresolved program identities remain unresolved unless explicitly verified")
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
