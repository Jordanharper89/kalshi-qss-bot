from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path

BUILD_ID='OAD-337'
TITLE='SOLANA PROGRAM DECODE PHYSICAL COVERAGE GATE'
EXPECTED='build_oad_337_solana_program_decode_physical_coverage_gate.py'
MODULE='oad_337_solana_program_decode_physical_coverage_gate.py'
TEST='test_oad_337_solana_program_decode_physical_coverage_gate.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py': ('acquire_finalized_block_batch',), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('canonical_transaction_envelopes',), 'qseries_v2/oracle_adapters/independent/oad_334_solana_transaction_protocol_attribution.py': ('attribute_transaction_protocols',), 'qseries_v2/oracle_adapters/independent/oad_335_solana_jupiter_route_reconstruction.py': ('reconstruct_routed_swaps',), 'qseries_v2/oracle_adapters/independent/oad_336_solana_pump_meteora_market_behavior_decoder.py': ('decode_protocol_market_behaviors',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_320_solana_program_instruction_registry import classify_transaction_instructions
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_333_solana_authoritative_program_identity_registry import identify_solana_program
from .oad_334_solana_transaction_protocol_attribution import attribute_transaction_protocols
from .oad_335_solana_jupiter_route_reconstruction import reconstruct_routed_swaps
from .oad_336_solana_pump_meteora_market_behavior_decoder import decode_protocol_market_behaviors

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
BASELINE_KNOWN_RATIO=0.5804145818441744

@dataclass(frozen=True,slots=True)
class SolanaProgramDecodePhysicalReport:
    blocks:int
    transactions:int
    instructions:int
    baseline_known_ratio:float
    prior_registry_known:int
    authoritative_known:int
    infrastructure_instructions:int
    economic_known_instructions:int
    unknown_instructions:int
    authoritative_known_ratio:float
    economic_resolution_ratio:float
    wallet_flows:int
    routed_swaps:int
    protocol_behaviors:int
    protocol_counts:tuple
    top_unknown_programs:tuple
    materially_improved:bool
    state:str
    execution_authority:bool=False

def measure_solana_program_decode_physical(block_limit=1,timeout_seconds=25.0):
    batch=acquire_finalized_block_batch(None,block_limit,timeout_seconds)
    env=canonical_transaction_envelopes(batch)
    legacy=classify_transaction_instructions(env)
    attr=attribute_transaction_protocols(env)
    flows=build_wallet_token_flows(env)
    routes=reconstruct_routed_swaps(env,attr,flows)
    behaviors=decode_protocol_market_behaviors(env,attr,flows)

    # Count exact top-level + CPI program invocations from the attribution layer.
    ids=[]
    for a in attr:
        ids.extend(a.top_level_program_ids)
        ids.extend(a.inner_program_ids)
    infra=econ=unknown=0
    pc=Counter(); uc=Counter()
    for pid in ids:
        x=identify_solana_program(pid)
        if not x.known:
            unknown+=1;uc[pid]+=1
        elif x.category=="INFRASTRUCTURE":
            infra+=1;pc[x.name]+=1
        else:
            econ+=1;pc[x.name]+=1
    total=len(ids)
    known=infra+econ
    ratio=known/total if total else 1.0
    econ_denom=econ+unknown
    economic_ratio=econ/econ_denom if econ_denom else 1.0
    prior_known=sum(1 for x in legacy if x.program_class!="UNKNOWN_PROGRAM")
    improved=ratio>BASELINE_KNOWN_RATIO
    state="PROGRAM_DECODE_COVERAGE_MEASURED" if env and total else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY"
    return SolanaProgramDecodePhysicalReport(
        len(batch.blocks),len(env),total,BASELINE_KNOWN_RATIO,prior_known,known,infra,econ,unknown,
        ratio,economic_ratio,len(flows),len(routes),len(behaviors),
        tuple(pc.most_common()),tuple(uc.most_common(20)),improved,state,False
    )

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_337_solana_program_decode_physical_coverage_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  x=measure_solana_program_decode_physical(block_limit=1)
  print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.instructions)
  print("[PHYSICAL] baseline_known_ratio=",x.baseline_known_ratio)
  print("[PHYSICAL] authoritative_known_ratio=",x.authoritative_known_ratio,"economic_resolution_ratio=",x.economic_resolution_ratio)
  print("[PHYSICAL] infrastructure=",x.infrastructure_instructions,"economic_known=",x.economic_known_instructions,"unknown=",x.unknown_instructions)
  print("[PHYSICAL] wallet_flows=",x.wallet_flows,"routed_swaps=",x.routed_swaps,"protocol_behaviors=",x.protocol_behaviors)
  print("[PHYSICAL] protocol_counts=",x.protocol_counts)
  print("[PHYSICAL] top_unknown_programs=",x.top_unknown_programs[:10])
  print("[PHYSICAL] materially_improved=",x.materially_improved,"state=",x.state)
  self.assertGreater(x.transactions,0)
  self.assertGreater(x.instructions,0)
  self.assertEqual(x.state,"PROGRAM_DECODE_COVERAGE_MEASURED")
  self.assertGreaterEqual(x.authoritative_known_ratio,0.0)
  self.assertLessEqual(x.authoritative_known_ratio,1.0)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-337 physical Solana program/protocol decode coverage measured")
 print("[PASS] infrastructure traffic separated from unresolved economic traffic")
 print("[PASS] top unknown programs retained for next evidence-driven decoder expansion")

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

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"
    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]",r)
    for rel,marks in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file():
            raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src:
                raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_332_solana_live_decode_coverage_physical_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    targets=(m,t,init)
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines:
            lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] OAD-327 continuity and OAD-332 live baseline preserved unchanged")
        print("[PASS] program attribution includes top-level + inner/CPI instructions")
        print("[PASS] unknown programs retained; infrastructure separated from economic traffic")
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
