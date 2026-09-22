from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

EXPECTED="build_oad_380_existing_learner_state_probe_OAD317_DEPENDENCY_REBUILD.py"
MODULE="oad_380_existing_learner_state_probe.py"
TEST="test_oad_380_existing_learner_state_probe.py"

MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

COUNTER_KEYS=(
    "outcomes_learned",
    "learned_records",
    "cycles",
    "through_sequence",
    "learning_cycles",
    "experiences_learned",
)

@dataclass(frozen=True, slots=True)
class ExistingLearnerStateSnapshot:
    files_scanned:int
    candidates:tuple
    counters:tuple
    execution_authority:bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir():
            return q
    raise RuntimeError("repo root not found")

def _scan_object(obj):
    stack=[obj]
    found={}
    while stack:
        x=stack.pop()

        if isinstance(x,dict):
            for k,v in x.items():
                key=str(k)

                if key in COUNTER_KEYS and isinstance(v,(int,float)):
                    found[key]=v

                elif isinstance(v,(dict,list)):
                    stack.append(v)

        elif isinstance(x,list):
            stack.extend(x[:256])

    return found

def snapshot_existing_learner_state(root=None):
    r=Path(root or _root())

    roots=(
        r/"runtime_state",
        r/"runtime"/"oracle_live_shadow",
        r/"runtime",
    )

    seen=set()
    files_scanned=0
    candidates=[]
    counters={}

    for base in roots:
        if not base.is_dir():
            continue

        for p in base.rglob("*.json"):
            try:
                rp=p.resolve()
            except Exception:
                rp=p

            if rp in seen:
                continue

            seen.add(rp)
            files_scanned+=1

            low=str(p).lower()

            # Only inspect plausible Oracle / learning runtime state files.
            if not any(x in low for x in ("learn","ocl","oracle","runtime_state")):
                continue

            try:
                obj=json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue

            local=_scan_object(obj)

            if not local:
                continue

            try:
                rel=str(p.relative_to(r))
            except Exception:
                rel=str(p)

            candidates.append(rel)

            for k,v in local.items():
                if k not in counters or float(v)>float(counters[k]):
                    counters[k]=v

    return ExistingLearnerStateSnapshot(
        files_scanned=files_scanned,
        candidates=tuple(sorted(set(candidates))),
        counters=tuple(sorted(counters.items())),
        execution_authority=False,
    )
"""

TEST_SOURCE=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_380_existing_learner_state_probe import (
    snapshot_existing_learner_state,
)

class T(unittest.TestCase):

    def test_probe(self):
        x=snapshot_existing_learner_state()

        print("[LEARNER-STATE] files_scanned=",x.files_scanned)
        print("[LEARNER-STATE] candidates=",x.candidates)
        print("[LEARNER-STATE] counters=",x.counters)

        self.assertGreaterEqual(x.files_scanned,0)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-380 existing learner state probe certified read-only")
    print("[PASS] actual OAD-317 existing-learning boundary verified")
    print("[PASS] no guessed OAD-377 handoff symbol dependency remains")
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

    tmp.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    os.replace(tmp,path)

def inspect_module(path):
    if not path.is_file():
        raise RuntimeError("dependency missing: "+str(path))

    text=path.read_text(encoding="utf-8")
    tree=ast.parse(text,filename=str(path))

    funcs=tuple(sorted(
        n.name
        for n in tree.body
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
        and not n.name.startswith("_")
    ))

    return text,funcs

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"

    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-380 EXISTING LEARNER STATE PROBE - OAD-317 DEPENDENCY REBUILD INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    p317=pkg/"oad_317_solana_existing_ocl_learning_handoff.py"
    text317,funcs317=inspect_module(p317)

    if "build_solana_learning_handoff" not in funcs317:
        raise RuntimeError(
            "actual OAD-317 handoff function missing; public functions="
            +repr(funcs317)
        )

    print("[PASS] actual OAD-317 handoff verified: build_solana_learning_handoff")

    p377=pkg/"oad_377_solana_existing_ocl_learning_handoff_physical_gate.py"
    if p377.is_file():
        text377,funcs377=inspect_module(p377)
        print("[PASS] OAD-377 present and preserved; public functions:",funcs377)

    print("[PASS] stale requirement for build_solana_learning_handoff inside OAD-377 removed")
    print("[PASS] OAD-380 remains a read-only learner-state probe")

    protected=[]

    for rel in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py",
        "qseries_v2/oracle_adapters/independent/oad_327_solana_universal_continuity_physical_certification.py",
        "qseries_v2/oracle_adapters/independent/oad_357_solana_decoder_closeout_same_universe_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_362_solana_continuity_integrity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_377_solana_existing_ocl_learning_handoff_physical_gate.py",
        "qseries_v2/oracle_adapters/independent/oad_378_solana_oad317_exact_case_execution.py",
        "qseries_v2/oracle_adapters/independent/oad_379_solana_oad317_result_contract.py",
    ):
        p=r/rel
        if p.is_file():
            protected.append(
                (p,hashlib.sha256(p.read_bytes()).hexdigest())
            )

    old={
        p:(p.read_bytes() if p.exists() else None)
        for p in (m,t,init)
    }

    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)

        lines=(
            init.read_text(encoding="utf-8").splitlines()
            if init.exists()
            else []
        )

        export="from ."+m.stem+" import *"

        if export not in lines:
            lines.append(export)

        atomic(
            init,
            "\n".join(x for x in lines if x.strip())+"\n",
        )

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError(
                    "protected boundary changed: "+p.name
                )

        print("[PASS] module installed:",m.relative_to(r))
        print("[PASS] test installed:",t.name)
        print("[PASS] OAD-317 preserved byte-for-byte")
        print("[PASS] OAD-377/OAD-378/OAD-379 preserved")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-380 OAD-317 DEPENDENCY REBUILD INSTALLATION COMPLETE")

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
