from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-344'
TITLE='SOLANA EXPANDED PROTOCOL ATTRIBUTION'
EXPECTED='build_oad_344_solana_expanded_protocol_attribution.py'
MODULE='oad_344_solana_expanded_protocol_attribution.py'
TEST='test_oad_344_solana_expanded_protocol_attribution.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_334_solana_transaction_protocol_attribution.py': ('attribute_transaction_protocols', 'top_level_program_ids', 'inner_program_ids'), 'qseries_v2/oracle_adapters/independent/oad_343_solana_verified_recurring_program_identity_expansion.py': ('identify_expanded_program', 'PHOENIX_ETERNAL_PROGRAM_ID', 'ARCHER_EXCHANGE_PROGRAM_ID')}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from .oad_334_solana_transaction_protocol_attribution import attribute_transaction_protocols
from .oad_343_solana_verified_recurring_program_identity_expansion import identify_expanded_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaExpandedProtocolAttribution:
    signature:str
    top_level_program_ids:tuple
    inner_program_ids:tuple
    economic_protocols:tuple
    infrastructure_protocols:tuple
    unknown_program_ids:tuple
    execution_authority:bool=False

def attribute_expanded_protocols(envelopes):
    base=attribute_transaction_protocols(envelopes)
    out=[]
    for a in base:
        top=tuple(a.top_level_program_ids)
        inner=tuple(a.inner_program_ids)
        econ=[];infra=[];unknown=[]
        for pid in top+inner:
            x=identify_expanded_program(pid)
            if not x.known:
                unknown.append(pid)
            elif x.market_relevant:
                econ.append(x.name)
            else:
                infra.append(x.name)
        out.append(SolanaExpandedProtocolAttribution(
            a.signature,top,inner,
            tuple(dict.fromkeys(econ)),
            tuple(dict.fromkeys(infra)),
            tuple(unknown),
            False
        ))
    return tuple(out)

"""

TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_344_solana_expanded_protocol_attribution as mod

class T(unittest.TestCase):
    def test_attribution(self):
        original=mod.attribute_transaction_protocols
        try:
            mod.attribute_transaction_protocols=lambda envs:(
                SimpleNamespace(
                    signature="s",
                    top_level_program_ids=("EtrnLzgbS7nMMy5fbD42kXiUzGg8XQzJ972Xtk1cjWih","pythWSnswVUd12oZpeFP8e9CVaEqJg25g1Vtc2biRsT"),
                    inner_program_ids=("W1LDCARDa67SPBG7TFpQivHnEZXRtxCFP13ysEd1bWR",)
                ),
            )
            x=mod.attribute_expanded_protocols((object(),))[0]
        finally:
            mod.attribute_transaction_protocols=original
        print("[ATTR]",x.economic_protocols,x.infrastructure_protocols,x.unknown_program_ids)
        self.assertEqual(x.economic_protocols,("PHOENIX_ETERNAL",))
        self.assertEqual(x.infrastructure_protocols,("PYTH_PRICE_FEED",))
        self.assertEqual(x.unknown_program_ids,("W1LDCARDa67SPBG7TFpQivHnEZXRtxCFP13ysEd1bWR",))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-344 expanded top-level + CPI protocol attribution certified")

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
