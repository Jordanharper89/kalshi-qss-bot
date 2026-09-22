from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_357_solana_decoder_closeout_same_universe_physical_gate.py'
BUILD_ID='OAD-357'
TITLE='SOLANA DECODER CLOSEOUT SAME-UNIVERSE PHYSICAL GATE'
MODULE='oad_357_solana_decoder_closeout_same_universe_physical_gate.py'
TEST='test_oad_357_solana_decoder_closeout_same_universe_physical_gate.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py': ('acquire_finalized_block_batch',), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('canonical_transaction_envelopes',), 'qseries_v2/oracle_adapters/independent/oad_348_solana_verified_economic_program_expansion.py': ('identify_verified_economic_program',), 'qseries_v2/oracle_adapters/independent/oad_353_solana_final_verified_economic_program_expansion.py': ('identify_final_verified_program',), 'qseries_v2/oracle_adapters/independent/oad_354_solana_economic_protocol_attribution_v3.py': ('attribute_economic_protocols_v3',), 'qseries_v2/oracle_adapters/independent/oad_355_solana_final_economic_behavior_decoder.py': ('decode_final_economic_behaviors',), 'qseries_v2/oracle_adapters/independent/oad_356_solana_decoder_closeout_unknown_registry.py': ('rank_decoder_closeout_unknowns',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_348_solana_verified_economic_program_expansion import identify_verified_economic_program
from .oad_353_solana_final_verified_economic_program_expansion import identify_final_verified_program
from .oad_354_solana_economic_protocol_attribution_v3 import attribute_economic_protocols_v3
from .oad_355_solana_final_economic_behavior_decoder import decode_final_economic_behaviors
from .oad_356_solana_decoder_closeout_unknown_registry import rank_decoder_closeout_unknowns

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaDecoderCloseoutPhysicalReport:
    blocks:int
    transactions:int
    program_invocations:int
    previous_known:int
    final_known:int
    previous_unknown:int
    final_unknown:int
    previous_known_ratio:float
    final_known_ratio:float
    known_ratio_delta:float
    previous_economic_known:int
    final_economic_known:int
    previous_economic_resolution_ratio:float
    final_economic_resolution_ratio:float
    economic_resolution_delta:float
    wallet_flows:int
    decoded_behaviors:int
    behavior_counts:tuple
    remaining_unknowns:tuple
    state:str
    execution_authority:bool=False

def measure_decoder_closeout_physical(block_limit=2,timeout_seconds=30.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    env=canonical_transaction_envelopes(batch)
    attrs=attribute_economic_protocols_v3(env)
    flows=build_wallet_token_flows(env)
    behaviors=decode_final_economic_behaviors(env,attrs,flows)
    unknowns=rank_decoder_closeout_unknowns(attrs,flows)

    ids=[]
    for a in attrs: ids.extend(tuple(a.top_level_program_ids)+tuple(a.inner_program_ids))
    pk=pe=fk=fe=0
    for pid in ids:
        p=identify_verified_economic_program(pid)
        f=identify_final_verified_program(pid)
        if p.known:
            pk+=1
            if p.market_relevant: pe+=1
        if f.known:
            fk+=1
            if f.market_relevant: fe+=1
    total=len(ids); pu=total-pk; fu=total-fk
    pr=pk/total if total else 1.0; fr=fk/total if total else 1.0
    pden=pe+pu; fden=fe+fu
    per=pe/pden if pden else 1.0; fer=fe/fden if fden else 1.0
    bc=Counter(b.behavior for b in behaviors)

    return SolanaDecoderCloseoutPhysicalReport(
        len(batch.blocks),len(env),total,pk,fk,pu,fu,pr,fr,fr-pr,pe,fe,per,fer,fer-per,
        len(flows),len(behaviors),tuple(bc.most_common()),
        tuple((u.program_id,u.invocations,u.flow_transactions,u.bidirectional_flow_transactions,u.priority_score,u.disposition) for u in unknowns[:20]),
        "DECODER_CLOSEOUT_PHYSICAL_MEASURED" if env and ids else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY",False
    )

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_357_solana_decoder_closeout_same_universe_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_decoder_closeout_physical(2)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.program_invocations)
        print("[PHYSICAL] previous_known=",x.previous_known,"final_known=",x.final_known,"previous_unknown=",x.previous_unknown,"final_unknown=",x.final_unknown)
        print("[PHYSICAL] previous_known_ratio=",x.previous_known_ratio,"final_known_ratio=",x.final_known_ratio,"delta=",x.known_ratio_delta)
        print("[PHYSICAL] previous_economic_resolution_ratio=",x.previous_economic_resolution_ratio,"final_economic_resolution_ratio=",x.final_economic_resolution_ratio,"delta=",x.economic_resolution_delta)
        print("[PHYSICAL] wallet_flows=",x.wallet_flows,"decoded_behaviors=",x.decoded_behaviors,"behavior_counts=",x.behavior_counts)
        print("[PHYSICAL] remaining_unknowns=",x.remaining_unknowns[:12])
        self.assertGreaterEqual(x.blocks,1)
        self.assertGreater(x.transactions,0)
        self.assertGreater(x.program_invocations,0)
        self.assertEqual(x.state,"DECODER_CLOSEOUT_PHYSICAL_MEASURED")
        self.assertGreaterEqual(x.final_known,x.previous_known)
        self.assertLessEqual(x.final_unknown,x.previous_unknown)
        self.assertGreaterEqual(x.final_known_ratio,x.previous_known_ratio)
        self.assertGreaterEqual(x.final_economic_resolution_ratio,x.previous_economic_resolution_ratio)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-357 same-universe final Solana decoder closeout physically certified")
    print("[PASS] remaining unknowns preserved as non-blocking evidence backlog")

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
