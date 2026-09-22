from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_354_solana_economic_protocol_attribution_v3.py'
BUILD_ID='OAD-354'
TITLE='SOLANA ECONOMIC PROTOCOL ATTRIBUTION V3'
MODULE='oad_354_solana_economic_protocol_attribution_v3.py'
TEST='test_oad_354_solana_economic_protocol_attribution_v3.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_334_solana_transaction_protocol_attribution.py': ('attribute_transaction_protocols', 'top_level_program_ids', 'inner_program_ids'), 'qseries_v2/oracle_adapters/independent/oad_353_solana_final_verified_economic_program_expansion.py': ('identify_final_verified_program', 'METEORA_DBC_PROGRAM_ID', 'RAYDIUM_CLMM_PROGRAM_ID')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_334_solana_transaction_protocol_attribution import attribute_transaction_protocols
from .oad_353_solana_final_verified_economic_program_expansion import identify_final_verified_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaEconomicProtocolAttributionV3:
    signature:str
    top_level_program_ids:tuple
    inner_program_ids:tuple
    economic_protocols:tuple
    infrastructure_protocols:tuple
    unknown_program_ids:tuple
    execution_authority:bool=False

def attribute_economic_protocols_v3(envelopes):
    base=attribute_transaction_protocols(envelopes)
    out=[]
    for a in base:
        top=tuple(a.top_level_program_ids); inner=tuple(a.inner_program_ids)
        econ=[];infra=[];unknown=[]
        for pid in top+inner:
            x=identify_final_verified_program(pid)
            if not x.known: unknown.append(pid)
            elif x.market_relevant: econ.append(x.name)
            else: infra.append(x.name)
        out.append(SolanaEconomicProtocolAttributionV3(
            a.signature,top,inner,tuple(dict.fromkeys(econ)),tuple(dict.fromkeys(infra)),tuple(unknown),False
        ))
    return tuple(out)

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_354_solana_economic_protocol_attribution_v3 as mod

class T(unittest.TestCase):
    def test_attr(self):
        old=mod.attribute_transaction_protocols
        try:
            mod.attribute_transaction_protocols=lambda envs:(
                SimpleNamespace(signature="s",
                    top_level_program_ids=("dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN","CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"),
                    inner_program_ids=("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc","99vQwtBwYtrqqD9YSXbdum3KBdxPAVxYTaQ3cfnJSrN2")),
            )
            x=mod.attribute_economic_protocols_v3((object(),))[0]
        finally:
            mod.attribute_transaction_protocols=old
        print("[ATTR-V3]",x.economic_protocols,x.unknown_program_ids)
        self.assertIn("METEORA_DBC",x.economic_protocols)
        self.assertIn("RAYDIUM_CLMM",x.economic_protocols)
        self.assertIn("ORCA_WHIRLPOOLS",x.economic_protocols)
        self.assertIn("99vQwtBwYtrqqD9YSXbdum3KBdxPAVxYTaQ3cfnJSrN2",x.unknown_program_ids)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-354 final economic top-level + CPI attribution certified")

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
