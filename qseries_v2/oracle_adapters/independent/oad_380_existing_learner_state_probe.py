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
