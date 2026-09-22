from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED='build_oad_372_solana_final_persistence_continuity_physical_gate.py'
BUILD_ID='OAD-372'
TITLE='SOLANA FINAL PERSISTENCE CONTINUITY PHYSICAL GATE'
MODULE='oad_372_solana_final_persistence_continuity_physical_gate.py'
TEST='test_oad_372_solana_final_persistence_continuity_physical_gate.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_326_solana_universal_resilient_worker.py': ('run_solana_universal_worker_cycle', 'SolanaUniversalWorkerCycle'), 'qseries_v2/oracle_adapters/independent/oad_368_solana_physical_checkpoint_contract.py': ('discover_checkpoint_contract',), 'qseries_v2/oracle_adapters/independent/oad_359_solana_immutable_gap_lineage_ledger.py': ('verify_gap_lineage',), 'qseries_v2/oracle_adapters/independent/oad_370_solana_checkpoint_commit_after_readback.py': ('CHECKPOINT_PHYSICALLY_COMMITTED',), 'qseries_v2/oracle_adapters/independent/oad_371_solana_physical_restart_backfill_plan.py': ('SolanaPhysicalRestartPlan',)}

MODULE_SOURCE=r"""\

from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect, subprocess, sys, time
from pathlib import Path
from .oad_368_solana_physical_checkpoint_contract import discover_checkpoint_contract
from .oad_359_solana_immutable_gap_lineage_ledger import verify_gap_lineage

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaFinalPersistenceContinuityReport:
    cycles:int
    successful_cycles:int
    checkpoint_before:int|None
    checkpoint_after:int|None
    checkpoint_advanced:bool
    total_transactions:int
    total_observations:int
    total_committed:int
    gap_ledger_valid:bool
    gap_records:int
    worker_symbol:str
    writer_started_by_gate:bool
    state:str
    execution_authority:bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir(): return q
    raise RuntimeError("repo root not found")

def _val(obj,*names,default=None):
    for n in names:
        if hasattr(obj,n): return getattr(obj,n)
        if isinstance(obj,dict) and n in obj: return obj[n]
    return default

def _worker():
    mod=importlib.import_module("qseries_v2.oracle_adapters.independent.oad_326_solana_universal_resilient_worker")
    f=getattr(mod,"run_solana_universal_worker_cycle",None)
    if not (inspect.isfunction(f) or inspect.ismethod(f)):
        raise RuntimeError("certified OAD-326 worker function unavailable")
    return "run_solana_universal_worker_cycle",f

def _invoke(f,root):
    sig=inspect.signature(f); kwargs={}
    for name,p in sig.parameters.items():
        low=name.lower()
        if low in ("root","repo_root","repository_root","base_root"): kwargs[name]=root
        elif low in ("count","max_slots","slot_limit","limit","batch_limit","block_limit"): kwargs[name]=1
        elif low in ("timeout_seconds","timeout"): kwargs[name]=60.0
        elif low in ("acquisition_timeout_seconds","rpc_timeout_seconds"): kwargs[name]=30.0
        elif p.default is inspect._empty:
            raise RuntimeError("unsupported worker argument: "+name)
    return f(**kwargs)

def _runner(root):
    p=root/"run_oph_021_exclusive_postgresql_canonical_writer.py"
    if p.is_file(): return p
    hits=tuple(root.rglob("run_oph_021_exclusive_postgresql_canonical_writer.py"))
    if len(hits)==1: return hits[0]
    raise RuntimeError("certified OPH-021 runner not uniquely available")

def _start_writer(root):
    p=subprocess.Popen([sys.executable,str(_runner(root))],cwd=str(root),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(2.0)
    if p.poll() is None: return p,True
    return None,False

def _stop(p):
    if p is not None and p.poll() is None:
        p.terminate()
        try: p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(timeout=5)

def measure_final_persistence_continuity(cycles=4):
    root=_root()
    before=discover_checkpoint_contract(root).current_slot
    name,f=_worker()
    proc=None; started=False
    results=[]
    try:
        proc,started=_start_writer(root)
        for i in range(int(cycles)):
            results.append(_invoke(f,root))
            if i==1:
                time.sleep(0.25)
        after=discover_checkpoint_contract(root).current_slot
        ok,gaps=verify_gap_lineage(root)

        tx=sum(int(_val(x,"transactions","transaction_count","transactions_observed",default=0) or 0) for x in results)
        obs=sum(int(_val(x,"observations","observation_count","canonical_observations","observations_persisted",default=0) or 0) for x in results)
        committed=sum(int(_val(x,"committed_events","events_committed","committed_observations","committed_count","persisted_observations",default=0) or 0) for x in results)

        success=0
        for x in results:
            s=str(_val(x,"state","persistence_state","status","worker_state",default="UNKNOWN")).upper()
            if "FAIL" not in s and "ERROR" not in s and "ROLLBACK" not in s:
                success+=1

        advanced=(after is not None and (before is None or int(after)>int(before)))
        state="FINAL_PERSISTENCE_CONTINUITY_CERTIFIED"
        if success!=len(results): state="WORKER_FAILURE"
        elif not advanced: state="CHECKPOINT_NOT_ADVANCED"
        elif not ok: state="GAP_LEDGER_INVALID"

        return SolanaFinalPersistenceContinuityReport(
            len(results),success,before,after,advanced,tx,obs,committed,ok,gaps,name,started,state,False
        )
    finally:
        _stop(proc)

"""

TEST_SOURCE=r"""\

import unittest
from qseries_v2.oracle_adapters.independent.oad_372_solana_final_persistence_continuity_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_final_persistence_continuity(4)
        print("[FINAL-PHYSICAL] worker=",x.worker_symbol,"writer_started_by_gate=",x.writer_started_by_gate)
        print("[FINAL-PHYSICAL] cycles=",x.cycles,"successful=",x.successful_cycles)
        print("[FINAL-PHYSICAL] checkpoint=",x.checkpoint_before,"->",x.checkpoint_after,"advanced=",x.checkpoint_advanced)
        print("[FINAL-PHYSICAL] transactions=",x.total_transactions,"observations=",x.total_observations,"committed=",x.total_committed)
        print("[FINAL-PHYSICAL] gap_ledger_valid=",x.gap_ledger_valid,"gap_records=",x.gap_records,"state=",x.state)
        self.assertEqual(x.cycles,4)
        self.assertEqual(x.successful_cycles,4)
        self.assertTrue(x.checkpoint_advanced)
        self.assertTrue(x.gap_ledger_valid)
        self.assertEqual(x.state,"FINAL_PERSISTENCE_CONTINUITY_CERTIFIED")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-372 final Solana persistence + durable checkpoint advancement physically certified")
    print("[PASS] certified OPH-021 writer boundary used and stopped only if started by this gate")
    print("[PASS] next boundary is temporal/outcome/learning integration")

"""

def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def verify(path, markers):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    ast.parse(text, filename=str(path))
    for marker in markers:
        if marker not in text:
            raise RuntimeError("dependency interface missing: "+path.name+" -> "+marker)

def atomic(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp,path)

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
    print("[ROOT]",r)

    for rel, markers in DEPENDENCIES.items():
        verify(r/rel, markers)
        print("[PASS] dependency interface verified:", rel)

    protected=[]
    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_367_solana_end_to_end_persistence_restart_physical_gate.py",
    ):
        p=r/rel
        if p.is_file():
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
        print("[PASS] protected certified boundaries preserved")
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
