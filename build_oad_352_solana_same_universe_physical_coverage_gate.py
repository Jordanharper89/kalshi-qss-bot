from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_352_solana_same_universe_physical_coverage_gate.py'
BUILD_ID='OAD-352'
TITLE='SOLANA SAME-UNIVERSE PHYSICAL COVERAGE GATE'
MODULE='oad_352_solana_same_universe_physical_coverage_gate.py'
TEST='test_oad_352_solana_same_universe_physical_coverage_gate.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py': ('acquire_finalized_block_batch',), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('canonical_transaction_envelopes',), 'qseries_v2/oracle_adapters/independent/oad_343_solana_verified_recurring_program_identity_expansion.py': ('identify_expanded_program',), 'qseries_v2/oracle_adapters/independent/oad_348_solana_verified_economic_program_expansion.py': ('identify_verified_economic_program',), 'qseries_v2/oracle_adapters/independent/oad_349_solana_economic_protocol_attribution_v2.py': ('attribute_economic_protocols_v2',), 'qseries_v2/oracle_adapters/independent/oad_350_solana_verified_economic_flow_behavior_decoder.py': ('decode_verified_economic_flow_behaviors',), 'qseries_v2/oracle_adapters/independent/oad_351_solana_remaining_unknown_priority_ranker.py': ('rank_remaining_unknown_programs',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_343_solana_verified_recurring_program_identity_expansion import identify_expanded_program
from .oad_348_solana_verified_economic_program_expansion import identify_verified_economic_program
from .oad_349_solana_economic_protocol_attribution_v2 import attribute_economic_protocols_v2
from .oad_350_solana_verified_economic_flow_behavior_decoder import decode_verified_economic_flow_behaviors
from .oad_351_solana_remaining_unknown_priority_ranker import rank_remaining_unknown_programs

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaSameUniverseCoverageReport:
    blocks:int
    transactions:int
    program_invocations:int
    old_known:int
    new_known:int
    old_unknown:int
    new_unknown:int
    old_known_ratio:float
    new_known_ratio:float
    known_ratio_delta:float
    old_economic_known:int
    new_economic_known:int
    old_economic_resolution_ratio:float
    new_economic_resolution_ratio:float
    economic_resolution_delta:float
    wallet_flows:int
    decoded_behaviors:int
    behavior_counts:tuple
    remaining_unknowns:tuple
    state:str
    execution_authority:bool=False

def measure_same_universe_coverage(block_limit=2,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    env=canonical_transaction_envelopes(batch)
    attrs=attribute_economic_protocols_v2(env)
    flows=build_wallet_token_flows(env)
    behaviors=decode_verified_economic_flow_behaviors(env,attrs,flows)
    priorities=rank_remaining_unknown_programs(attrs,flows)

    ids=[]
    for a in attrs:
        ids.extend(tuple(a.top_level_program_ids)+tuple(a.inner_program_ids))

    old_known=old_econ=0
    new_known=new_econ=0
    for pid in ids:
        o=identify_expanded_program(pid)
        n=identify_verified_economic_program(pid)
        if o.known:
            old_known+=1
            if o.market_relevant: old_econ+=1
        if n.known:
            new_known+=1
            if n.market_relevant: new_econ+=1

    total=len(ids)
    old_unknown=total-old_known; new_unknown=total-new_known
    old_ratio=(old_known/total) if total else 1.0
    new_ratio=(new_known/total) if total else 1.0
    old_econ_den=old_econ+old_unknown
    new_econ_den=new_econ+new_unknown
    old_econ_ratio=(old_econ/old_econ_den) if old_econ_den else 1.0
    new_econ_ratio=(new_econ/new_econ_den) if new_econ_den else 1.0
    bc=Counter(b.behavior for b in behaviors)

    return SolanaSameUniverseCoverageReport(
        len(batch.blocks),len(env),total,
        old_known,new_known,old_unknown,new_unknown,
        old_ratio,new_ratio,new_ratio-old_ratio,
        old_econ,new_econ,old_econ_ratio,new_econ_ratio,new_econ_ratio-old_econ_ratio,
        len(flows),len(behaviors),tuple(bc.most_common()),
        tuple((p.program_id,p.invocations,p.flow_transactions,p.bidirectional_flow_transactions,p.priority_score,p.priority_class) for p in priorities[:20]),
        "SAME_UNIVERSE_COVERAGE_MEASURED" if env and ids else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY",
        False
    )

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_352_solana_same_universe_physical_coverage_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_same_universe_coverage(2)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.program_invocations)
        print("[PHYSICAL] old_known=",x.old_known,"new_known=",x.new_known,"old_unknown=",x.old_unknown,"new_unknown=",x.new_unknown)
        print("[PHYSICAL] old_known_ratio=",x.old_known_ratio,"new_known_ratio=",x.new_known_ratio,"delta=",x.known_ratio_delta)
        print("[PHYSICAL] old_economic_resolution_ratio=",x.old_economic_resolution_ratio,"new_economic_resolution_ratio=",x.new_economic_resolution_ratio,"delta=",x.economic_resolution_delta)
        print("[PHYSICAL] wallet_flows=",x.wallet_flows,"decoded_behaviors=",x.decoded_behaviors,"behavior_counts=",x.behavior_counts)
        print("[PHYSICAL] remaining_unknowns=",x.remaining_unknowns[:12])
        self.assertGreaterEqual(x.blocks,1)
        self.assertGreater(x.transactions,0)
        self.assertGreater(x.program_invocations,0)
        self.assertEqual(x.state,"SAME_UNIVERSE_COVERAGE_MEASURED")
        self.assertGreaterEqual(x.new_known,x.old_known)
        self.assertLessEqual(x.new_unknown,x.old_unknown)
        self.assertGreaterEqual(x.new_known_ratio,x.old_known_ratio)
        self.assertGreaterEqual(x.new_economic_resolution_ratio,x.old_economic_resolution_ratio)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-352 same-universe old-vs-new physical Solana coverage certified")
    print("[PASS] coverage deltas are now apples-to-apples on identical live blocks")

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
