from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-346'
TITLE='SOLANA UNRESOLVED ECONOMIC EVIDENCE PROFILER'
EXPECTED='build_oad_346_solana_unresolved_economic_evidence_profiler.py'
MODULE='oad_346_solana_unresolved_economic_evidence_profiler.py'
TEST='test_oad_346_solana_unresolved_economic_evidence_profiler.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_344_solana_expanded_protocol_attribution.py': ('unknown_program_ids', 'SolanaExpandedProtocolAttribution'), 'qseries_v2/oracle_adapters/independent/oad_330_solana_wallet_token_flow_graph.py': ('build_wallet_token_flows',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter,defaultdict

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaUnresolvedEconomicEvidence:
    program_id:str
    invocations:int
    transactions:int
    transactions_with_token_flows:int
    flow_rows:int
    distinct_mints:int
    bidirectional_flow_transactions:int
    evidence_class:str
    execution_authority:bool=False

def profile_unresolved_economic_evidence(envelopes,attributions,flows):
    flow_by_sig=defaultdict(list)
    for f in flows:
        flow_by_sig[f.signature].append(f)
    sigs_by_program=defaultdict(set)
    inv=Counter()
    for a in attributions:
        for pid in a.unknown_program_ids:
            inv[pid]+=1
            sigs_by_program[pid].add(a.signature)
    out=[]
    for pid,count in inv.most_common():
        sigs=sigs_by_program[pid]
        rows=[];mints=set();with_flow=0;bidir=0
        for sig in sigs:
            fs=flow_by_sig.get(sig,[])
            if fs:
                with_flow+=1
                rows.extend(fs)
                mints.update(str(f.mint) for f in fs if getattr(f,"mint",None))
                pos=any(float(getattr(f,"delta",0.0))>0 for f in fs)
                neg=any(float(getattr(f,"delta",0.0))<0 for f in fs)
                if pos and neg:
                    bidir+=1
        evidence="NO_TOKEN_FLOW_EVIDENCE"
        if with_flow:
            evidence="TOKEN_FLOW_ASSOCIATED_UNKNOWN_PROGRAM"
        if bidir:
            evidence="BIDIRECTIONAL_TOKEN_FLOW_ASSOCIATED_UNKNOWN_PROGRAM"
        out.append(SolanaUnresolvedEconomicEvidence(
            pid,count,len(sigs),with_flow,len(rows),len(mints),bidir,evidence,False
        ))
    return tuple(out)

"""

TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_346_solana_unresolved_economic_evidence_profiler import *

class T(unittest.TestCase):
    def test_profile(self):
        attrs=(SimpleNamespace(signature="s",unknown_program_ids=("X","X")),)
        flows=(SimpleNamespace(signature="s",mint="A",delta=-1.0),SimpleNamespace(signature="s",mint="B",delta=1.0))
        x=profile_unresolved_economic_evidence((),attrs,flows)[0]
        print("[UNKNOWN-EVIDENCE]",x.program_id,x.invocations,x.evidence_class)
        self.assertEqual(x.program_id,"X")
        self.assertEqual(x.invocations,2)
        self.assertEqual(x.bidirectional_flow_transactions,1)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-346 unresolved-program economic evidence profiler certified")
    print("[PASS] evidence is measured without assigning unverified protocol identities")

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
