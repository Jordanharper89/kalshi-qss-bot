from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_348_solana_verified_economic_program_expansion.py'
BUILD_ID='OAD-348'
TITLE='SOLANA VERIFIED ECONOMIC PROGRAM EXPANSION'
MODULE='oad_348_solana_verified_economic_program_expansion.py'
TEST='test_oad_348_solana_verified_economic_program_expansion.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_343_solana_verified_recurring_program_identity_expansion.py': ('identify_expanded_program', 'SolanaExpandedProgramIdentity'), 'qseries_v2/oracle_adapters/independent/oad_347_solana_expanded_decode_multiblock_physical_gate.py': ('top_unresolved_economic_evidence', 'EXPANDED_PROGRAM_DECODE_COVERAGE_MEASURED')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_343_solana_verified_recurring_program_identity_expansion import identify_expanded_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

TESSERA_V_PROGRAM_ID="TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH"
BISONFI_PROGRAM_ID="BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi"
OKX_LABS_2_PROGRAM_ID="proVF4pMXVaYqmy4NjniPh4pqKNfMmsihgd4wdkCX3u"
DFLOW_AGGREGATOR_V4_PROGRAM_ID="DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH"
HUMIDIFI_PROGRAM_ID="9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp"

@dataclass(frozen=True,slots=True)
class SolanaVerifiedEconomicProgramIdentity:
    program_id:str
    name:str
    category:str
    known:bool
    market_relevant:bool
    evidence_class:str
    execution_authority:bool=False

_VERIFIED={
    TESSERA_V_PROGRAM_ID:("TESSERA_V","ECONOMIC_PROGRAM",True,"PUBLIC_EXPLORER_LABEL"),
    BISONFI_PROGRAM_ID:("BISONFI","DEX_OR_SWAP_PROGRAM",True,"PUBLIC_EXPLORER_LABEL_PLUS_SWAP_LOG_EVIDENCE"),
    OKX_LABS_2_PROGRAM_ID:("OKX_LABS_2","ECONOMIC_PROGRAM",True,"PUBLIC_EXPLORER_LABEL"),
    DFLOW_AGGREGATOR_V4_PROGRAM_ID:("DFLOW_AGGREGATOR_V4","DEX_AGGREGATOR",True,"PROGRAM_REFERENCE_PLUS_VERIFIED_BUILD"),
    HUMIDIFI_PROGRAM_ID:("HUMIDIFI","PRIVATE_AMM",True,"PUBLIC_PROGRAM_REFERENCE"),
}

def identify_verified_economic_program(program_id):
    pid=str(program_id or "")
    base=identify_expanded_program(pid)
    if base.known:
        return SolanaVerifiedEconomicProgramIdentity(
            pid,base.name,base.category,True,base.market_relevant,
            "OAD_343",False
        )
    x=_VERIFIED.get(pid)
    if x:
        return SolanaVerifiedEconomicProgramIdentity(pid,x[0],x[1],True,x[2],x[3],False)
    return SolanaVerifiedEconomicProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False,"UNRESOLVED",False)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_348_solana_verified_economic_program_expansion import *

class T(unittest.TestCase):
    def test_verified(self):
        rows=(
            identify_verified_economic_program(TESSERA_V_PROGRAM_ID),
            identify_verified_economic_program(BISONFI_PROGRAM_ID),
            identify_verified_economic_program(OKX_LABS_2_PROGRAM_ID),
            identify_verified_economic_program(DFLOW_AGGREGATOR_V4_PROGRAM_ID),
            identify_verified_economic_program(HUMIDIFI_PROGRAM_ID),
        )
        print("[VERIFIED]",tuple((x.name,x.category) for x in rows))
        self.assertTrue(all(x.known and x.market_relevant for x in rows))
        self.assertEqual(identify_verified_economic_program("FLUX6xBayGxLX9UcimVRxXFMHH6q43mAbRvDzSpCsvfK").name,"UNRESOLVED")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-348 verified economically active Solana identity expansion certified")
    print("[PASS] FLUX and other weaker-evidence IDs intentionally remain unresolved")

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
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    s=path.read_text(encoding="utf-8")
    ast.parse(s,filename=str(path))
    for m in markers:
        if m not in s:
            raise RuntimeError("dependency contract missing: "+path.name+" -> "+m)

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,markers in DEPENDENCIES.items():
        verify(r/rel,markers)
        print("[PASS] dependency interface verified:",rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_342_solana_foundation_repair_physical_coverage_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_347_solana_expanded_decode_multiblock_physical_gate.py",
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
        print("[PASS] frozen/proven Solana boundaries preserved unchanged")
        print("[PASS] no guessed identity promotion")
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
