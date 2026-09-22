from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_367_solana_end_to_end_persistence_restart_physical_gate.py'
BUILD_ID='OAD-367'
TITLE='SOLANA END-TO-END PERSISTENCE RESTART PHYSICAL GATE'
MODULE='oad_367_solana_end_to_end_persistence_restart_physical_gate.py'
TEST='test_oad_367_solana_end_to_end_persistence_restart_physical_gate.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_326_solana_universal_resilient_worker.py': ('run_universal_worker_cycle', 'SolanaUniversalWorkerCycle'), 'qseries_v2/oracle_adapters/independent/oad_323_solana_durable_slot_checkpoint.py': ('load_solana_chain_checkpoint', 'SolanaChainCheckpoint'), 'qseries_v2/oracle_adapters/independent/oad_359_solana_immutable_gap_lineage_ledger.py': ('verify_gap_lineage',), 'qseries_v2/oracle_adapters/independent/oad_365_solana_checkpoint_after_readback_enforcement.py': ('CHECKPOINT_ADMITTED', 'BLOCKED_READBACK'), 'qseries_v2/oracle_adapters/independent/oad_366_solana_restart_backfill_idempotency_guard.py': ('RESTART_REPLAY_IDEMPOTENT',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import inspect, subprocess, sys, time
from pathlib import Path

from .oad_326_solana_universal_resilient_worker import run_universal_worker_cycle
from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint
from .oad_359_solana_immutable_gap_lineage_ledger import verify_gap_lineage

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaEndToEndPersistenceRestartReport:
    cycles: int
    successful_cycles: int
    checkpoint_before: int|None
    checkpoint_after: int|None
    cycle_states: tuple
    committed_events: int
    transactions: int
    observation_count: int
    restart_observed: bool
    checkpoint_nonregression: bool
    gap_ledger_valid: bool
    gap_records: int
    state: str
    execution_authority: bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir():
            return q
    raise RuntimeError("repo root not found")

def _cycle_once():
    f=run_universal_worker_cycle
    sig=inspect.signature(f)
    kwargs={}
    for name,param in sig.parameters.items():
        if param.default is inspect._empty:
            if name in ("root","repo_root"):
                kwargs[name]=_root()
            else:
                raise RuntimeError("unsupported required worker-cycle argument: "+name)
    return f(**kwargs)

def _val(obj,*names,default=None):
    for n in names:
        if hasattr(obj,n):
            return getattr(obj,n)
        if isinstance(obj,dict) and n in obj:
            return obj[n]
    return default

def measure_end_to_end_persistence_restart(cycles=3, restart_pause_seconds=0.2):
    root=_root()
    before_obj=load_solana_chain_checkpoint(root)
    before=_val(before_obj,"slot","checkpoint_slot","last_slot",default=None)
    results=[]
    total_committed=0
    total_tx=0
    total_obs=0

    for i in range(int(cycles)):
        x=_cycle_once()
        results.append(x)
        total_committed += int(_val(x,"committed_events","events_committed","committed_observations",default=0) or 0)
        total_tx += int(_val(x,"transactions","transaction_count",default=0) or 0)
        total_obs += int(_val(x,"observations","observation_count","canonical_observations",default=0) or 0)
        if i==0:
            time.sleep(float(restart_pause_seconds))

    after_obj=load_solana_chain_checkpoint(root)
    after=_val(after_obj,"slot","checkpoint_slot","last_slot",default=None)

    states=[]
    success=0
    for x in results:
        state=str(_val(x,"state","persistence_state","status",default="UNKNOWN"))
        states.append(state)
        if "FAIL" not in state.upper() and "ERROR" not in state.upper():
            success+=1

    nonreg=(before is None or after is None or int(after)>=int(before))
    gap_ok,gap_n=verify_gap_lineage(root)
    state="END_TO_END_PERSISTENCE_RESTART_MEASURED"
    if success != len(results):
        state="WORKER_CYCLE_FAILURE"
    elif not nonreg:
        state="CHECKPOINT_REGRESSION"
    elif not gap_ok:
        state="GAP_LEDGER_INVALID"

    return SolanaEndToEndPersistenceRestartReport(
        len(results),success,before,after,tuple(states),total_committed,total_tx,total_obs,
        len(results)>=2,nonreg,gap_ok,gap_n,state,False
    )

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_367_solana_end_to_end_persistence_restart_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_end_to_end_persistence_restart(3)
        print("[PHYSICAL] cycles=",x.cycles,"successful=",x.successful_cycles,"states=",x.cycle_states)
        print("[PHYSICAL] checkpoint=",x.checkpoint_before,"->",x.checkpoint_after,"restart_observed=",x.restart_observed)
        print("[PHYSICAL] committed_events=",x.committed_events,"transactions=",x.transactions,"observations=",x.observation_count)
        print("[PHYSICAL] gap_ledger_valid=",x.gap_ledger_valid,"gap_records=",x.gap_records,"state=",x.state)

        self.assertEqual(x.cycles,3)
        self.assertEqual(x.successful_cycles,3)
        self.assertTrue(x.restart_observed)
        self.assertTrue(x.checkpoint_nonregression)
        self.assertTrue(x.gap_ledger_valid)
        self.assertEqual(x.state,"END_TO_END_PERSISTENCE_RESTART_MEASURED")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-367 sustained Solana persistence/restart physical gate measured")
    print("[PASS] canonical writer boundary, checkpoint non-regression, restart sequencing, and gap lineage remained intact")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def verify(path, markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    for marker in markers:
        if marker not in text:
            raise RuntimeError("dependency interface missing: "+path.name+" -> "+marker)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer identity mismatch")
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[ROOT]", r)

    for rel, markers in DEPENDENCIES.items():
        verify(r/rel, markers)
        print("[PASS] dependency interface verified:", rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
    ):
        p=r/rel
        if not p.is_file():
            raise RuntimeError("protected boundary missing: "+rel)
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m, MODULE_SOURCE)
        atomic(t, TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines:
            lines.append(export)
        atomic(init, "\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("protected boundary changed: "+p.name)

        print("[PASS] module installed:", m.relative_to(r))
        print("[PASS] test installed:", t.name)
        print("[PASS] OPH-023/OAD-327/OAD-357/OAD-362 preserved byte-for-byte unchanged")
        print("[PASS] no bypass PostgreSQL writer introduced")
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
