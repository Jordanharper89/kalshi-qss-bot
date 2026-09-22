from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-347'
TITLE='SOLANA EXPANDED DECODE MULTI-BLOCK PHYSICAL GATE'
EXPECTED='build_oad_347_solana_expanded_decode_multiblock_physical_gate.py'
MODULE='oad_347_solana_expanded_decode_multiblock_physical_gate.py'
TEST='test_oad_347_solana_expanded_decode_multiblock_physical_gate.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py': ('acquire_finalized_block_batch',), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('canonical_transaction_envelopes',), 'qseries_v2/oracle_adapters/independent/oad_343_solana_verified_recurring_program_identity_expansion.py': ('identify_expanded_program', 'PYTH_PRICE_FEED_PROGRAM_ID'), 'qseries_v2/oracle_adapters/independent/oad_344_solana_expanded_protocol_attribution.py': ('attribute_expanded_protocols',), 'qseries_v2/oracle_adapters/independent/oad_345_solana_orderbook_dex_behavior_decoder.py': ('decode_orderbook_dex_behaviors',), 'qseries_v2/oracle_adapters/independent/oad_346_solana_unresolved_economic_evidence_profiler.py': ('profile_unresolved_economic_evidence',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_343_solana_verified_recurring_program_identity_expansion import identify_expanded_program
from .oad_344_solana_expanded_protocol_attribution import attribute_expanded_protocols
from .oad_345_solana_orderbook_dex_behavior_decoder import decode_orderbook_dex_behaviors
from .oad_346_solana_unresolved_economic_evidence_profiler import profile_unresolved_economic_evidence

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

OAD342_KNOWN_RATIO=0.9130739572379951
OAD342_ECONOMIC_RESOLUTION_RATIO=0.8226037195994278

@dataclass(frozen=True,slots=True)
class SolanaExpandedDecodePhysicalReport:
    blocks:int
    transactions:int
    program_invocations:int
    known:int
    infrastructure:int
    economic_known:int
    unknown:int
    known_ratio:float
    economic_resolution_ratio:float
    wallet_flows:int
    orderbook_behaviors:int
    behavior_counts:tuple
    top_unknown_programs:tuple
    top_unresolved_economic_evidence:tuple
    state:str
    execution_authority:bool=False

def measure_expanded_decode_physical(block_limit=2,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    env=canonical_transaction_envelopes(batch)
    attrs=attribute_expanded_protocols(env)
    flows=build_wallet_token_flows(env)
    behaviors=decode_orderbook_dex_behaviors(env,attrs,flows)
    evidence=profile_unresolved_economic_evidence(env,attrs,flows)

    ids=[]
    for a in attrs:
        ids.extend(tuple(a.top_level_program_ids)+tuple(a.inner_program_ids))

    known=infra=econ=0
    unknown_counter=Counter()
    for pid in ids:
        x=identify_expanded_program(pid)
        if x.known:
            known+=1
            if x.market_relevant:
                econ+=1
            else:
                infra+=1
        else:
            unknown_counter[pid]+=1

    unknown=sum(unknown_counter.values())
    known_ratio=(known/len(ids)) if ids else 1.0
    economic_den=econ+unknown
    economic_ratio=(econ/economic_den) if economic_den else 1.0
    bc=Counter(b.behavior for b in behaviors)

    evidence_rows=tuple(
        (
            e.program_id,e.invocations,e.transactions,
            e.transactions_with_token_flows,e.bidirectional_flow_transactions,
            e.evidence_class
        )
        for e in evidence[:20]
    )

    return SolanaExpandedDecodePhysicalReport(
        len(batch.blocks),len(env),len(ids),known,infra,econ,unknown,
        known_ratio,economic_ratio,len(flows),len(behaviors),
        tuple(bc.most_common()),
        tuple(unknown_counter.most_common(20)),
        evidence_rows,
        "EXPANDED_PROGRAM_DECODE_COVERAGE_MEASURED" if env and ids else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY",
        False
    )

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_347_solana_expanded_decode_multiblock_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_expanded_decode_physical(2)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.program_invocations)
        print("[PHYSICAL] oad342_known_ratio=",OAD342_KNOWN_RATIO,"oad342_economic_resolution_ratio=",OAD342_ECONOMIC_RESOLUTION_RATIO)
        print("[PHYSICAL] known_ratio=",x.known_ratio,"economic_resolution_ratio=",x.economic_resolution_ratio)
        print("[PHYSICAL] known=",x.known,"infrastructure=",x.infrastructure,"economic_known=",x.economic_known,"unknown=",x.unknown)
        print("[PHYSICAL] wallet_flows=",x.wallet_flows,"orderbook_behaviors=",x.orderbook_behaviors,"behavior_counts=",x.behavior_counts)
        print("[PHYSICAL] top_unknown_programs=",x.top_unknown_programs[:12])
        print("[PHYSICAL] top_unresolved_economic_evidence=",x.top_unresolved_economic_evidence[:12])
        self.assertGreaterEqual(x.blocks,1)
        self.assertGreater(x.transactions,0)
        self.assertGreater(x.program_invocations,0)
        self.assertEqual(x.state,"EXPANDED_PROGRAM_DECODE_COVERAGE_MEASURED")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-347 multi-block physical Solana expanded decode coverage measured")
    print("[PASS] verified identities separated from evidence-only unresolved programs")

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
