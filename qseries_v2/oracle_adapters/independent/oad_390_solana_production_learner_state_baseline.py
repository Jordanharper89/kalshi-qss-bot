from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
from .oad_388_solana_production_learner_exact_admission_topology_audit import audit_production_learner_topology

READ_ONLY=True
EXECUTION_AUTHORITY=False
COUNTER_KEYS=("outcomes_learned","learned_records","cycles","through_sequence","learning_cycles","experiences_learned")

@dataclass(frozen=True, slots=True)
class LearnerStateBaseline:
    files:tuple
    counters:tuple
    execution_authority:bool=False

def _root(root=None):
    if root is not None: return Path(root).resolve()
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("repo root not found")

def capture_learner_state_baseline(root=None):
    r=_root(root); topo=audit_production_learner_topology(r)
    counters=[]
    for rel in topo.runtime_state_files:
        p=r/rel
        try: data=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        def walk(x,prefix=""):
            if isinstance(x,dict):
                for k,v in x.items():
                    path=f"{prefix}.{k}" if prefix else k
                    if k in COUNTER_KEYS and isinstance(v,(int,float)):
                        counters.append((rel,path,v))
                    walk(v,path)
            elif isinstance(x,list):
                for i,v in enumerate(x): walk(v,f"{prefix}[{i}]")
        walk(data)
    return LearnerStateBaseline(tuple(topo.runtime_state_files),tuple(counters),False)
