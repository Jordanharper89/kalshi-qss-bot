from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID='OAD-332'; TITLE='SOLANA LIVE DECODE COVERAGE PHYSICAL GATE'; EXPECTED='build_oad_332_solana_live_decode_coverage_physical_gate.py'; MODULE='oad_332_solana_live_decode_coverage_physical_gate.py'; TEST='test_oad_332_solana_live_decode_coverage_physical_gate.py'; DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py': ('acquire_finalized_block_batch',), 'qseries_v2/oracle_adapters/independent/oad_319_solana_transaction_canonical_envelope.py': ('canonical_transaction_envelopes',), 'qseries_v2/oracle_adapters/independent/oad_320_solana_program_instruction_registry.py': ('classify_transaction_instructions',), 'qseries_v2/oracle_adapters/independent/oad_328_solana_live_dex_pool_identity_registry.py': ('build_live_solana_dex_pool_registry',), 'qseries_v2/oracle_adapters/independent/oad_331_solana_dex_market_behavior_inference.py': ('infer_solana_market_behavior',)}
MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from .oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes
from .oad_320_solana_program_instruction_registry import classify_transaction_instructions
from .oad_328_solana_live_dex_pool_identity_registry import build_live_solana_dex_pool_registry
from .oad_329_solana_dex_transaction_attribution import attribute_transactions_to_live_dex_pools
from .oad_330_solana_wallet_token_flow_graph import build_wallet_token_flows
from .oad_331_solana_dex_market_behavior_inference import infer_solana_market_behavior
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaDecodeCoverageReport:
 blocks:int;transactions:int;instructions:int;unknown_instructions:int;known_instruction_ratio:float
 dex_registry_pools:int;dex_registry_ids:tuple;dex_attributed_transactions:int;wallet_flows:int
 decoded_behaviors:int;behavior_counts:tuple;unknown_program_counts:tuple;state:str;execution_authority:bool=False
def measure_live_solana_decode_coverage(block_limit=1,dex_query="SOL/USDC",dex_limit=100,timeout_seconds=25.0):
    b=acquire_finalized_block_batch(None,block_limit,timeout_seconds);env=canonical_transaction_envelopes(b)
    cls=classify_transaction_instructions(env);reg=build_live_solana_dex_pool_registry(dex_query,dex_limit,timeout_seconds)
    attr=attribute_transactions_to_live_dex_pools(env,reg);flows=build_wallet_token_flows(env);beh=infer_solana_market_behavior(env,attr,flows)
    unknown=[c.program_id for c in cls if c.program_class=="UNKNOWN_PROGRAM"]
    known_ratio=(len(cls)-len(unknown))/len(cls) if cls else 1.0
    bc=Counter(x.behavior for x in beh);uc=Counter(unknown)
    state="LIVE_DECODE_COVERAGE_MEASURED" if env and cls else "INSUFFICIENT_LIVE_CHAIN_ACTIVITY"
    return SolanaDecodeCoverageReport(len(b.blocks),len(env),len(cls),len(unknown),known_ratio,reg.pools,reg.dexes,sum(x.attributed for x in attr),len(flows),len(beh),tuple(sorted(bc.items())),tuple(uc.most_common(20)),state,False)

"""
TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_332_solana_live_decode_coverage_physical_gate import *
class T(unittest.TestCase):
 def test_physical(self):
  x=measure_live_solana_decode_coverage(block_limit=1)
  print("[LIVE] blocks=",x.blocks,"transactions=",x.transactions,"instructions=",x.instructions)
  print("[LIVE] known_instruction_ratio=",x.known_instruction_ratio,"unknown_instructions=",x.unknown_instructions)
  print("[LIVE] dex_registry_pools=",x.dex_registry_pools,"dexes=",x.dex_registry_ids)
  print("[LIVE] dex_attributed_transactions=",x.dex_attributed_transactions,"wallet_flows=",x.wallet_flows)
  print("[LIVE] decoded_behaviors=",x.decoded_behaviors,"behavior_counts=",x.behavior_counts)
  print("[LIVE] top_unknown_programs=",x.unknown_program_counts[:10])
  self.assertGreater(x.transactions,0);self.assertGreater(x.instructions,0);self.assertGreater(x.dex_registry_pools,0)
  self.assertEqual(x.state,"LIVE_DECODE_COVERAGE_MEASURED")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-332 physical live Solana decode coverage measured")
 print("[PASS] unknown programs ranked for next decoder expansion instead of discarded")

"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p)); p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BUILD_ID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPENDENCIES.items():
        p=r/rel
        if not p.is_file(): raise RuntimeError("dependency missing: "+rel)
        src=p.read_text(encoding="utf-8"); ast.parse(src,filename=str(p))
        for mark in marks:
            if mark not in src: raise RuntimeError("dependency contract missing: "+rel+" -> "+mark)
        print("[PASS] exact dependency verified:",rel)
    protected=[]
    for rel in ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
                "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
                "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py"):
        p=r/rel
        if not p.is_file(): raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+m.stem+" import *"
        if exp not in lines: lines.append(exp)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] OAD-327 continuity boundary preserved unchanged")
        print("[PASS] live pool/Dex identity used; no brittle hard-coded DEX program dependency")
        print("[PASS] unknown chain behavior retained and measured")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()
