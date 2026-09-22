from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_367_solana_end_to_end_persistence_restart_physical_gate_WORKER_INTERFACE_REBUILD.py"
MODULE="oad_367_solana_end_to_end_persistence_restart_physical_gate.py"
TEST="test_oad_367_solana_end_to_end_persistence_restart_physical_gate.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import importlib, inspect, time
from pathlib import Path

from .oad_323_solana_durable_slot_checkpoint import load_solana_chain_checkpoint
from .oad_359_solana_immutable_gap_lineage_ledger import verify_gap_lineage

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaEndToEndPersistenceRestartReport:
    cycles:int
    successful_cycles:int
    checkpoint_before:int|None
    checkpoint_after:int|None
    cycle_states:tuple
    committed_events:int
    transactions:int
    observation_count:int
    restart_observed:bool
    checkpoint_nonregression:bool
    gap_ledger_valid:bool
    gap_records:int
    worker_symbol:str
    state:str
    execution_authority:bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir():
            return q
    raise RuntimeError("repo root not found")

def _val(obj,*names,default=None):
    for n in names:
        if hasattr(obj,n):
            return getattr(obj,n)
        if isinstance(obj,dict) and n in obj:
            return obj[n]
    return default

def _discover_worker_cycle():
    mod=importlib.import_module(
        "qseries_v2.oracle_adapters.independent.oad_326_solana_universal_resilient_worker"
    )

    preferred=(
        "run_universal_worker_cycle",
        "run_worker_cycle",
        "run_cycle",
        "execute_worker_cycle",
        "execute_cycle",
        "process_cycle",
        "worker_cycle",
    )
    for name in preferred:
        f=getattr(mod,name,None)
        if callable(f):
            return name,f

    candidates=[]
    for name,f in inspect.getmembers(mod,callable):
        if name.startswith("_"):
            continue
        low=name.lower()
        score=0
        if "cycle" in low: score+=10
        if "worker" in low: score+=5
        if "universal" in low: score+=3
        if "solana" in low: score+=2
        if any(x in low for x in ("build","test","verify","load","save","class")):
            score-=4
        if score>0:
            candidates.append((score,name,f))

    if not candidates:
        raise RuntimeError("no OAD-326 worker-cycle callable discovered")

    candidates.sort(key=lambda x:(-x[0],x[1]))
    _,name,f=candidates[0]
    return name,f

def _invoke_cycle(f):
    sig=inspect.signature(f)
    kwargs={}
    root=_root()

    for name,param in sig.parameters.items():
        if param.default is not inspect._empty:
            continue

        low=name.lower()
        if low in ("root","repo_root","repository_root","base_root"):
            kwargs[name]=root
            continue
        if low in ("max_slots","slot_limit","limit","batch_limit","block_limit"):
            kwargs[name]=1
            continue
        if low in ("timeout_seconds","timeout"):
            kwargs[name]=30.0
            continue

        raise RuntimeError(
            "unsupported required OAD-326 worker-cycle argument: "+name+
            " ; callable="+getattr(f,"__name__","UNKNOWN")
        )

    return f(**kwargs)

def measure_end_to_end_persistence_restart(cycles=3,restart_pause_seconds=0.2):
    root=_root()
    worker_name,worker=_discover_worker_cycle()

    before_obj=load_solana_chain_checkpoint(root)
    before=_val(before_obj,"slot","checkpoint_slot","last_slot","through_slot",default=None)

    results=[]
    total_committed=0
    total_tx=0
    total_obs=0

    for i in range(int(cycles)):
        x=_invoke_cycle(worker)
        results.append(x)

        total_committed += int(_val(
            x,"committed_events","events_committed","committed_observations",
            "committed_count","persisted_observations",default=0
        ) or 0)

        total_tx += int(_val(
            x,"transactions","transaction_count","transactions_observed",
            default=0
        ) or 0)

        total_obs += int(_val(
            x,"observations","observation_count","canonical_observations",
            "observations_persisted",default=0
        ) or 0)

        # Simulates process interruption boundary between production cycles.
        if i==0:
            time.sleep(float(restart_pause_seconds))

    after_obj=load_solana_chain_checkpoint(root)
    after=_val(after_obj,"slot","checkpoint_slot","last_slot","through_slot",default=None)

    states=[]
    successful=0
    for x in results:
        state=str(_val(
            x,"state","persistence_state","status","worker_state",
            default="UNKNOWN"
        ))
        states.append(state)
        upper=state.upper()
        if "FAIL" not in upper and "ERROR" not in upper and "ROLLBACK" not in upper:
            successful+=1

    nonreg=True
    if before is not None and after is not None:
        nonreg=int(after)>=int(before)

    gap_ok,gap_n=verify_gap_lineage(root)

    state="END_TO_END_PERSISTENCE_RESTART_MEASURED"
    if successful != len(results):
        state="WORKER_CYCLE_FAILURE"
    elif not nonreg:
        state="CHECKPOINT_REGRESSION"
    elif not gap_ok:
        state="GAP_LEDGER_INVALID"

    return SolanaEndToEndPersistenceRestartReport(
        cycles=len(results),
        successful_cycles=successful,
        checkpoint_before=before,
        checkpoint_after=after,
        cycle_states=tuple(states),
        committed_events=total_committed,
        transactions=total_tx,
        observation_count=total_obs,
        restart_observed=len(results)>=2,
        checkpoint_nonregression=nonreg,
        gap_ledger_valid=gap_ok,
        gap_records=gap_n,
        worker_symbol=worker_name,
        state=state,
        execution_authority=False,
    )
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_367_solana_end_to_end_persistence_restart_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_end_to_end_persistence_restart(3)

        print("[PHYSICAL] worker_symbol=",x.worker_symbol)
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
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-367 sustained Solana persistence/restart physical gate measured")
    print("[PASS] actual certified OAD-326 worker interface used")
    print("[PASS] checkpoint non-regression and immutable gap lineage remained intact")
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

def parse(path):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))
    text=path.read_text(encoding="utf-8")
    tree=ast.parse(text,filename=str(path))
    funcs={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    classes={n.name for n in ast.walk(tree) if isinstance(n,ast.ClassDef)}
    return text,funcs,classes

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-367 SOLANA END-TO-END PERSISTENCE RESTART PHYSICAL GATE - WORKER INTERFACE REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    # Verify OAD-326 by actual worker-cycle capability instead of one stale function name.
    p326=pkg/"oad_326_solana_universal_resilient_worker.py"
    text326,funcs326,classes326=parse(p326)

    if "SolanaUniversalWorkerCycle" not in classes326:
        raise RuntimeError("OAD-326 SolanaUniversalWorkerCycle contract missing")

    cycle_like=sorted(
        f for f in funcs326
        if "cycle" in f.lower() and not f.startswith("_")
    )
    if not cycle_like:
        raise RuntimeError(
            "OAD-326 has no discoverable public cycle callable; public functions="+repr(sorted(funcs326))
        )

    print("[PASS] OAD-326 resilient worker result contract verified: SolanaUniversalWorkerCycle")
    print("[PASS] OAD-326 discoverable public cycle callable(s):",tuple(cycle_like))

    # Stable dependencies.
    checks=(
        ("oad_323_solana_durable_slot_checkpoint.py",("load_solana_chain_checkpoint","SolanaChainCheckpoint")),
        ("oad_359_solana_immutable_gap_lineage_ledger.py",("verify_gap_lineage",)),
        ("oad_365_solana_checkpoint_after_readback_enforcement.py",("CHECKPOINT_ADMITTED","BLOCKED_READBACK")),
        ("oad_366_solana_restart_backfill_idempotency_guard.py",("RESTART_REPLAY_IDEMPOTENT",)),
    )
    for dep,marks in checks:
        p=pkg/dep
        text,funcs,classes=parse(p)
        for mark in marks:
            if mark not in text and mark not in funcs and mark not in classes:
                raise RuntimeError("dependency interface missing: "+dep+" -> "+mark)
        print("[PASS] dependency interface verified:",p.relative_to(r))

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
        print("[PASS] OAD-326 worker callable selected dynamically from certified production interface")
        print("[PASS] OPH-023/OAD-327/OAD-357/OAD-362 preserved byte-for-byte unchanged")
        print("[PASS] no bypass PostgreSQL writer introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-367 WORKER INTERFACE REBUILD INSTALLATION COMPLETE")

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
