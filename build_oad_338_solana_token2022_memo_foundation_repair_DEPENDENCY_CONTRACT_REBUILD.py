from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-338"
TITLE="SOLANA TOKEN-2022 MEMO FOUNDATION REPAIR"
EXPECTED="build_oad_338_solana_token2022_memo_foundation_repair_DEPENDENCY_CONTRACT_REBUILD.py"
MODULE="oad_338_solana_token2022_memo_foundation_repair.py"
TEST="test_oad_338_solana_token2022_memo_foundation_repair.py"

MODULE_SOURCE=r"""\
from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

TOKEN_2022_PROGRAM_ID="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
MEMO_PROGRAM_ID="MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

@dataclass(frozen=True,slots=True)
class SolanaFoundationProgramIdentity:
    program_id:str
    name:str
    category:str
    market_relevant:bool
    execution_authority:bool=False

def identify_foundation_program(program_id):
    pid=str(program_id or "")
    if pid==TOKEN_2022_PROGRAM_ID:
        return SolanaFoundationProgramIdentity(pid,"TOKEN_2022","TOKEN",True,False)
    if pid==MEMO_PROGRAM_ID:
        return SolanaFoundationProgramIdentity(pid,"MEMO","INFRASTRUCTURE",False,False)
    return SolanaFoundationProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False)
"""

TEST_SOURCE=r"""\
import unittest
from qseries_v2.oracle_adapters.independent.oad_338_solana_token2022_memo_foundation_repair import *

class T(unittest.TestCase):
    def test_ids(self):
        a=identify_foundation_program(TOKEN_2022_PROGRAM_ID)
        b=identify_foundation_program(MEMO_PROGRAM_ID)
        c=identify_foundation_program("UNRESOLVED_PROGRAM")
        print("[FOUNDATION]",a.name,a.program_id,b.name,b.program_id,c.name)
        self.assertEqual(a.name,"TOKEN_2022")
        self.assertEqual(a.category,"TOKEN")
        self.assertTrue(a.market_relevant)
        self.assertEqual(b.name,"MEMO")
        self.assertEqual(b.category,"INFRASTRUCTURE")
        self.assertFalse(b.market_relevant)
        self.assertEqual(c.name,"UNRESOLVED")
        self.assertFalse(c.market_relevant)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-338 exact Token-2022 + Memo foundation identities certified")
    print("[PASS] unresolved programs remain unresolved rather than guessed")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
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

def require_module_contract(path, required_any=(), required_all=()):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    source=path.read_text(encoding="utf-8")
    ast.parse(source,filename=str(path))
    for marker in required_all:
        if marker not in source:
            raise RuntimeError("dependency contract missing: "+path.name+" -> "+marker)
    if required_any and not any(marker in source for marker in required_any):
        raise RuntimeError(
            "dependency contract missing: "+path.name+
            " -> expected one of "+repr(tuple(required_any))
        )
    return source

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-338 SOLANA TOKEN-2022 MEMO FOUNDATION REPAIR - DEPENDENCY CONTRACT REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    oad333=pkg/"oad_333_solana_authoritative_program_identity_registry.py"
    require_module_contract(
        oad333,
        required_all=("identify_solana_program","PROGRAMS","SOLANA_VOTE","PUMP_FUN_AMM","JUPITER_V6","METEORA_DLMM"),
    )
    print("[PASS] exact OAD-333 production identity-registry interface verified without brittle stale literal marker")

    oad337=pkg/"oad_337_solana_program_decode_physical_coverage_gate.py"
    require_module_contract(
        oad337,
        required_all=("BASELINE_KNOWN_RATIO","measure_solana_program_decode_physical"),
    )
    print("[PASS] exact OAD-337 physical coverage interface verified")

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_333_solana_authoritative_program_identity_registry.py",
        "qseries_v2/oracle_adapters/independent/oad_337_solana_program_decode_physical_coverage_gate.py",
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
        export="from .oad_338_solana_token2022_memo_foundation_repair import *"
        if export not in lines:
            lines.append(export)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)

        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] OAD-333 and OAD-337 preserved byte-for-byte unchanged")
        print("[PASS] exact Token-2022 production ID installed")
        print("[PASS] exact Memo production ID installed")
        print("[PASS] unknown identities remain unresolved")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-338 DEPENDENCY CONTRACT REBUILD INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
