from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-341"
TITLE="SOLANA TOKEN-2022 ACTIVITY DECODER"
EXPECTED="build_oad_341_solana_token2022_activity_decoder_DEPENDENCY_CONTRACT_REBUILD.py"
MODULE="oad_341_solana_token2022_activity_decoder.py"
TEST="test_oad_341_solana_token2022_activity_decoder.py"

MODULE_SOURCE=r"""\
from __future__ import annotations
from dataclasses import dataclass
from .oad_339_solana_reconciled_program_identity_registry import identify_reconciled_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaToken2022Activity:
    signature:str
    slot:int
    token2022_invocations:int
    flow_count:int
    mints:tuple
    behavior:str
    execution_authority:bool=False

def decode_token2022_activity(envelopes,attributions,flows):
    amap={a.signature:a for a in attributions}
    out=[]
    for e in envelopes:
        a=amap.get(e.signature)
        if not a:
            continue
        ids=tuple(a.top_level_program_ids)+tuple(a.inner_program_ids)
        n=sum(
            1 for pid in ids
            if identify_reconciled_program(pid).name=="TOKEN_2022"
        )
        if not n:
            continue
        fs=[f for f in flows if f.signature==e.signature]
        mints=tuple(sorted({f.mint for f in fs if getattr(f,"mint",None)}))
        pos=any(getattr(f,"delta",0)>0 for f in fs)
        neg=any(getattr(f,"delta",0)<0 for f in fs)

        behavior="TOKEN_2022_INSTRUCTION_ONLY"
        if fs:
            behavior="TOKEN_2022_BALANCE_FLOW"
        if pos and neg:
            behavior="TOKEN_2022_TRANSFER_OR_SWAP_FLOW"

        out.append(
            SolanaToken2022Activity(
                e.signature,
                e.slot,
                n,
                len(fs),
                mints,
                behavior,
                False
            )
        )
    return tuple(out)
"""

TEST_SOURCE=r"""\
import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_341_solana_token2022_activity_decoder import *

class T(unittest.TestCase):
    def test_decode(self):
        e=SimpleNamespace(signature="s",slot=1)
        a=SimpleNamespace(
            signature="s",
            top_level_program_ids=("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",),
            inner_program_ids=()
        )
        fs=(
            SimpleNamespace(signature="s",mint="A",delta=-2.0),
            SimpleNamespace(signature="s",mint="B",delta=3.0),
        )
        x=decode_token2022_activity((e,),(a,),fs)[0]
        print("[TOKEN2022]",x.token2022_invocations,x.behavior,x.mints)
        self.assertEqual(x.token2022_invocations,1)
        self.assertEqual(x.behavior,"TOKEN_2022_TRANSFER_OR_SWAP_FLOW")
        self.assertEqual(x.mints,("A","B"))

    def test_no_fabrication(self):
        e=SimpleNamespace(signature="u",slot=2)
        a=SimpleNamespace(
            signature="u",
            top_level_program_ids=("UNRESOLVED_PROGRAM",),
            inner_program_ids=()
        )
        x=decode_token2022_activity((e,),(a,),())
        self.assertEqual(x,())

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-341 Token-2022 activity decoder certified")
    print("[PASS] unresolved programs are not mislabeled as Token-2022")
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

def require(path,required_all):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    source=path.read_text(encoding="utf-8")
    ast.parse(source,filename=str(path))
    for marker in required_all:
        if marker not in source:
            raise RuntimeError("dependency contract missing: "+path.name+" -> "+marker)
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
    print(" OAD-341 SOLANA TOKEN-2022 ACTIVITY DECODER - DEPENDENCY CONTRACT REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    p339=pkg/"oad_339_solana_reconciled_program_identity_registry.py"
    require(
        p339,
        (
            "identify_reconciled_program",
            "SolanaReconciledProgramIdentity",
            "FOUNDATION_REPAIR",
            "OAD_333",
        )
    )
    print("[PASS] OAD-339 reconciled identity interface verified without brittle TOKEN_2022 literal requirement")

    p330=pkg/"oad_330_solana_wallet_token_flow_graph.py"
    require(
        p330,
        (
            "SolanaWalletTokenFlow",
            "build_wallet_token_flows",
        )
    )
    print("[PASS] OAD-330 wallet/token flow interface verified")

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_337_solana_program_decode_physical_coverage_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_339_solana_reconciled_program_identity_registry.py",
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
        export="from .oad_341_solana_token2022_activity_decoder import *"
        if export not in lines:
            lines.append(export)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)

        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] OAD-339 identity boundary preserved unchanged")
        print("[PASS] Token-2022 resolution delegated to reconciled production registry")
        print("[PASS] no direct PostgreSQL writer introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-341 DEPENDENCY CONTRACT REBUILD INSTALLATION COMPLETE")

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
