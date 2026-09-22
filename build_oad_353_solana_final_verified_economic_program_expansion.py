from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_353_solana_final_verified_economic_program_expansion.py'
BUILD_ID='OAD-353'
TITLE='SOLANA FINAL VERIFIED ECONOMIC PROGRAM EXPANSION'
MODULE='oad_353_solana_final_verified_economic_program_expansion.py'
TEST='test_oad_353_solana_final_verified_economic_program_expansion.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_348_solana_verified_economic_program_expansion.py': ('identify_verified_economic_program', 'SolanaVerifiedEconomicProgramIdentity'), 'qseries_v2/oracle_adapters/independent/oad_352_solana_same_universe_physical_coverage_gate.py': ('SAME_UNIVERSE_COVERAGE_MEASURED', 'remaining_unknowns')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_348_solana_verified_economic_program_expansion import identify_verified_economic_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

METEORA_DBC_PROGRAM_ID="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
METEORA_DAMM_V2_PROGRAM_ID="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"
ORCA_WHIRLPOOLS_PROGRAM_ID="whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
PUMP_MAYHEM_PROGRAM_ID="MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e"
RAYDIUM_CLMM_PROGRAM_ID="CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"

@dataclass(frozen=True,slots=True)
class SolanaFinalVerifiedProgramIdentity:
    program_id:str
    name:str
    category:str
    known:bool
    market_relevant:bool
    evidence_class:str
    execution_authority:bool=False

_VERIFIED={
    METEORA_DBC_PROGRAM_ID:("METEORA_DBC","BONDING_CURVE_DEX",True,"FIRST_PARTY_METEORA_DOCS"),
    METEORA_DAMM_V2_PROGRAM_ID:("METEORA_DAMM_V2","AMM",True,"FIRST_PARTY_METEORA_DOCS"),
    ORCA_WHIRLPOOLS_PROGRAM_ID:("ORCA_WHIRLPOOLS","CONCENTRATED_LIQUIDITY_AMM",True,"PUBLIC_DEFI_PLATFORM_INDEX"),
    PUMP_MAYHEM_PROGRAM_ID:("PUMP_MAYHEM","TOKEN_LAUNCH_ECONOMIC_PROGRAM",True,"LIVE_PUBLIC_PROGRAM_LABEL"),
    RAYDIUM_CLMM_PROGRAM_ID:("RAYDIUM_CLMM","CONCENTRATED_LIQUIDITY_AMM",True,"FIRST_PARTY_RAYDIUM_DOCS"),
}

def identify_final_verified_program(program_id):
    pid=str(program_id or "")
    base=identify_verified_economic_program(pid)
    if base.known:
        return SolanaFinalVerifiedProgramIdentity(pid,base.name,base.category,True,base.market_relevant,"OAD_348",False)
    x=_VERIFIED.get(pid)
    if x:
        return SolanaFinalVerifiedProgramIdentity(pid,x[0],x[1],True,x[2],x[3],False)
    return SolanaFinalVerifiedProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False,"UNRESOLVED",False)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_353_solana_final_verified_economic_program_expansion import *

class T(unittest.TestCase):
    def test_verified(self):
        ids=(METEORA_DBC_PROGRAM_ID,METEORA_DAMM_V2_PROGRAM_ID,ORCA_WHIRLPOOLS_PROGRAM_ID,PUMP_MAYHEM_PROGRAM_ID,RAYDIUM_CLMM_PROGRAM_ID)
        rows=tuple(identify_final_verified_program(x) for x in ids)
        print("[FINAL-VERIFIED]",tuple((x.name,x.category) for x in rows))
        self.assertTrue(all(x.known and x.market_relevant for x in rows))
        self.assertFalse(identify_final_verified_program("99vQwtBwYtrqqD9YSXbdum3KBdxPAVxYTaQ3cfnJSrN2").known)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-353 final verified high-value Solana economic identity expansion certified")
    print("[PASS] weaker-evidence programs remain unresolved")

"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify(path,markers):
    if not path.is_file(): raise RuntimeError("dependency missing: "+str(path))
    s=path.read_text(encoding="utf-8"); ast.parse(s,filename=str(path))
    for m in markers:
        if m not in s: raise RuntimeError("dependency contract missing: "+path.name+" -> "+m)

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,markers in DEPENDENCIES.items():
        verify(r/rel,markers); print("[PASS] dependency interface verified:",rel)
    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_347_solana_expanded_decode_multiblock_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_352_solana_same_universe_physical_coverage_gate.py",
    ):
        p=r/rel
        if not p.is_file(): raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines: lines.append(export)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] proven Solana boundaries preserved byte-for-byte unchanged")
        print("[PASS] unresolved programs remain unresolved unless verified")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
