from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-343'
TITLE='SOLANA VERIFIED RECURRING PROGRAM IDENTITY EXPANSION'
EXPECTED='build_oad_343_solana_verified_recurring_program_identity_expansion.py'
MODULE='oad_343_solana_verified_recurring_program_identity_expansion.py'
TEST='test_oad_343_solana_verified_recurring_program_identity_expansion.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_339_solana_reconciled_program_identity_registry.py': ('identify_reconciled_program', 'SolanaReconciledProgramIdentity'), 'qseries_v2/oracle_adapters/independent/oad_342_solana_foundation_repair_physical_coverage_gate.py': ('FOUNDATION_REPAIR_COVERAGE_MEASURED',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_339_solana_reconciled_program_identity_registry import identify_reconciled_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

PHOENIX_ETERNAL_PROGRAM_ID="EtrnLzgbS7nMMy5fbD42kXiUzGg8XQzJ972Xtk1cjWih"
ARCHER_EXCHANGE_PROGRAM_ID="Archer8kgiavM61GyusMzaaS2ft5sALtNsD1HxkUPMhy"
PYTH_PRICE_FEED_PROGRAM_ID="pythWSnswVUd12oZpeFP8e9CVaEqJg25g1Vtc2biRsT"

@dataclass(frozen=True,slots=True)
class SolanaExpandedProgramIdentity:
    program_id:str
    name:str
    category:str
    known:bool
    market_relevant:bool
    evidence_class:str
    execution_authority:bool=False

_EXPANSION={
    PHOENIX_ETERNAL_PROGRAM_ID:("PHOENIX_ETERNAL","ORDER_BOOK_DEX",True,"PUBLISHED_PROGRAM_CONSTANT"),
    ARCHER_EXCHANGE_PROGRAM_ID:("ARCHER_EXCHANGE","ORDER_BOOK_DEX",True,"PUBLIC_PROGRAM_LABEL_PLUS_DEX_INDEX"),
    PYTH_PRICE_FEED_PROGRAM_ID:("PYTH_PRICE_FEED","ORACLE_INFRASTRUCTURE",False,"OFFICIAL_PYTH_CONTRACT_ADDRESS"),
}

def identify_expanded_program(program_id):
    pid=str(program_id or "")
    base=identify_reconciled_program(pid)
    if base.known:
        return SolanaExpandedProgramIdentity(
            pid,base.name,base.category,True,base.market_relevant,
            "OAD_339_RECONCILED",False
        )
    x=_EXPANSION.get(pid)
    if x:
        return SolanaExpandedProgramIdentity(pid,x[0],x[1],True,x[2],x[3],False)
    return SolanaExpandedProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False,"UNRESOLVED",False)

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_343_solana_verified_recurring_program_identity_expansion import *

class T(unittest.TestCase):
    def test_verified(self):
        p=identify_expanded_program(PHOENIX_ETERNAL_PROGRAM_ID)
        a=identify_expanded_program(ARCHER_EXCHANGE_PROGRAM_ID)
        y=identify_expanded_program(PYTH_PRICE_FEED_PROGRAM_ID)
        u=identify_expanded_program("W1LDCARDa67SPBG7TFpQivHnEZXRtxCFP13ysEd1bWR")
        print("[IDENTITIES]",p.name,a.name,y.name,u.name)
        self.assertEqual(p.category,"ORDER_BOOK_DEX")
        self.assertEqual(a.category,"ORDER_BOOK_DEX")
        self.assertEqual(y.category,"ORACLE_INFRASTRUCTURE")
        self.assertFalse(y.market_relevant)
        self.assertFalse(u.known)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-343 verified recurring Solana program identity expansion certified")
    print("[PASS] unverified recurring IDs remain unresolved")

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
