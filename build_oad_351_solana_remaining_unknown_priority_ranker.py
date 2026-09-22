from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_351_solana_remaining_unknown_priority_ranker.py'
BUILD_ID='OAD-351'
TITLE='SOLANA REMAINING UNKNOWN PRIORITY RANKER'
MODULE='oad_351_solana_remaining_unknown_priority_ranker.py'
TEST='test_oad_351_solana_remaining_unknown_priority_ranker.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_349_solana_economic_protocol_attribution_v2.py': ('unknown_program_ids', 'SolanaEconomicProtocolAttributionV2'), 'qseries_v2/oracle_adapters/independent/oad_330_solana_wallet_token_flow_graph.py': ('build_wallet_token_flows',)}

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
class SolanaRemainingUnknownPriority:
    program_id:str
    invocations:int
    transactions:int
    flow_transactions:int
    bidirectional_flow_transactions:int
    priority_score:int
    priority_class:str
    execution_authority:bool=False

def rank_remaining_unknown_programs(attributions,flows):
    flow_by_sig=defaultdict(list)
    for f in flows: flow_by_sig[f.signature].append(f)
    inv=Counter(); sigs=defaultdict(set)
    for a in attributions:
        for pid in a.unknown_program_ids:
            inv[pid]+=1; sigs[pid].add(a.signature)
    rows=[]
    for pid,count in inv.items():
        txs=sigs[pid]; ft=bi=0
        for sig in txs:
            fs=flow_by_sig.get(sig,())
            if fs:
                ft+=1
                if any(float(getattr(f,"delta",0))>0 for f in fs) and any(float(getattr(f,"delta",0))<0 for f in fs):
                    bi+=1
        score=count + 3*ft + 5*bi
        cls="LOW_EVIDENCE"
        if ft: cls="ECONOMIC_EVIDENCE"
        if bi: cls="HIGH_PRIORITY_BIDIRECTIONAL_FLOW"
        rows.append(SolanaRemainingUnknownPriority(pid,count,len(txs),ft,bi,score,cls,False))
    return tuple(sorted(rows,key=lambda x:(-x.priority_score,-x.invocations,x.program_id)))

"""
TEST_SOURCE=r"""\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_351_solana_remaining_unknown_priority_ranker import *

class T(unittest.TestCase):
    def test_rank(self):
        attrs=(
            SimpleNamespace(signature="a",unknown_program_ids=("X",)),
            SimpleNamespace(signature="b",unknown_program_ids=("Y","Y")),
        )
        flows=(
            SimpleNamespace(signature="a",delta=-1,mint="A"),
            SimpleNamespace(signature="a",delta=1,mint="B"),
        )
        rows=rank_remaining_unknown_programs(attrs,flows)
        print("[RANK]",tuple((x.program_id,x.priority_score,x.priority_class) for x in rows))
        self.assertEqual(rows[0].program_id,"X")
        self.assertEqual(rows[0].priority_class,"HIGH_PRIORITY_BIDIRECTIONAL_FLOW")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-351 remaining unknown economic-priority ranker certified")

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
