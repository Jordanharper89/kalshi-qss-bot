from __future__ import annotations
from dataclasses import dataclass
import ast, json, re
from pathlib import Path

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ProductionLearnerTopology:
    olr044_path:str
    olr044_functions:tuple
    olr046_path:str
    olr046_functions:tuple
    candidate_runner_paths:tuple
    runtime_state_files:tuple
    runtime_state_keys:tuple
    execution_authority:bool=False

def _repo_root(root=None):
    if root is not None:
        return Path(root).resolve()
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def _functions(path):
    tree=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    return tuple(
        n.name for n in tree.body
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
    )

def _string_literals(path):
    tree=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    vals=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            vals.append(n.value)
    return tuple(vals)

def _runner_candidates(root, paths):
    out=[]
    for p in paths:
        txt=p.read_text(encoding="utf-8")
        for m in re.findall(r'["\\\']([^"\\\']+\.py)["\\\']',txt):
            q=(root/m).resolve() if not Path(m).is_absolute() else Path(m)
            if q.is_file():
                out.append(str(q.relative_to(root)))
    return tuple(dict.fromkeys(out))

def _runtime_state_inventory(root):
    keys=(
        "outcomes_learned",
        "learned_records",
        "cycles",
        "through_sequence",
        "learning_cycles",
        "experiences_learned",
    )
    files=[]
    found=set()

    for base in (
        root/"runtime_state",
        root/"runtime"/"oracle_live_shadow",
        root/"runtime",
    ):
        if not base.is_dir():
            continue
        for p in base.rglob("*.json"):
            try:
                txt=p.read_text(encoding="utf-8")
            except Exception:
                continue
            hit=[k for k in keys if f'"{k}"' in txt]
            if hit:
                files.append(str(p.relative_to(root)))
                found.update(hit)

    return tuple(sorted(dict.fromkeys(files))),tuple(sorted(found))

def audit_production_learner_topology(root=None):
    r=_repo_root(root)

    p44=r/"qseries_v2"/"oracle_learning"/"olr_044_continuous_learner_evidence_runtime_cutover.py"
    p46=r/"qseries_v2"/"oracle_learning"/"olr_046_oracle_live_evidence_learner_launcher_cutover.py"

    if not p44.is_file():
        raise RuntimeError("OLR-044 missing: "+str(p44))
    if not p46.is_file():
        raise RuntimeError("OLR-046 missing: "+str(p46))

    f44=_functions(p44)
    f46=_functions(p46)

    if "find_learning_runner" not in f44:
        raise RuntimeError("OLR-044 missing find_learning_runner")
    if "read_children" not in f46:
        raise RuntimeError("OLR-046 missing read_children")
    if "patch_learning_child" not in f46:
        raise RuntimeError("OLR-046 missing patch_learning_child")

    runners=_runner_candidates(r,(p44,p46))
    state_files,state_keys=_runtime_state_inventory(r)

    return ProductionLearnerTopology(
        olr044_path=str(p44.relative_to(r)),
        olr044_functions=f44,
        olr046_path=str(p46.relative_to(r)),
        olr046_functions=f46,
        candidate_runner_paths=runners,
        runtime_state_files=state_files,
        runtime_state_keys=state_keys,
        execution_authority=False,
    )
