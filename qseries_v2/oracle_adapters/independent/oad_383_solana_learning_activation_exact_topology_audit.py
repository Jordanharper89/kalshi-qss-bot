from __future__ import annotations
from dataclasses import dataclass
import ast, inspect, importlib.util, json
from pathlib import Path

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class PythonSurface:
    path:str
    functions:tuple
    classes:tuple
    imports:tuple

@dataclass(frozen=True, slots=True)
class LearningActivationTopology:
    oad317:PythonSurface
    solana_history_modules:tuple
    outcome_modules:tuple
    learner_modules:tuple
    runtime_state_candidates:tuple
    execution_authority:bool=False

def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir():
            return q
    raise RuntimeError("Q Series repository root not found")

def _surface(path,root):
    text=path.read_text(encoding="utf-8")
    tree=ast.parse(text,filename=str(path))

    funcs=[]
    classes=[]
    imports=[]

    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and not n.name.startswith("_"):
            args=[]
            for a in list(n.args.posonlyargs)+list(n.args.args):
                args.append(a.arg)
            if n.args.vararg:
                args.append("*"+n.args.vararg.arg)
            for a in n.args.kwonlyargs:
                args.append(a.arg)
            if n.args.kwarg:
                args.append("**"+n.args.kwarg.arg)
            funcs.append((n.name,tuple(args)))

        elif isinstance(n,ast.ClassDef) and not n.name.startswith("_"):
            classes.append(n.name)

        elif isinstance(n,ast.Import):
            imports.extend(alias.name for alias in n.names)

        elif isinstance(n,ast.ImportFrom):
            base=n.module or ""
            names=",".join(alias.name for alias in n.names)
            imports.append(base+":"+names)

    return PythonSurface(
        path=str(path.relative_to(root)),
        functions=tuple(funcs),
        classes=tuple(sorted(classes)),
        imports=tuple(imports),
    )

def _matching_modules(root,patterns):
    q=root/"qseries_v2"
    out=[]
    seen=set()

    for pattern in patterns:
        for p in q.rglob(pattern):
            if not p.is_file() or p.name.startswith("test_"):
                continue
            rp=p.resolve()
            if rp in seen:
                continue
            seen.add(rp)

            try:
                out.append(_surface(p,root))
            except Exception:
                continue

    return tuple(sorted(out,key=lambda x:x.path))

def _runtime_candidates(root):
    out=[]
    keys=("outcomes_learned","learned_records","through_sequence","learning_cycles","experiences_learned")

    bases=(
        root/"runtime_state",
        root/"runtime",
    )

    seen=set()

    for base in bases:
        if not base.is_dir():
            continue

        for p in list(base.rglob("*.json"))+list(base.rglob("*.jsonl")):
            try:
                rp=p.resolve()
            except Exception:
                rp=p

            if rp in seen:
                continue

            seen.add(rp)

            low=str(p).lower()
            if not any(x in low for x in ("learn","ocl","oracle")):
                continue

            hits=set()

            try:
                text=p.read_text(encoding="utf-8",errors="replace")
            except Exception:
                continue

            for k in keys:
                if k in text:
                    hits.add(k)

            if hits:
                try:
                    rel=str(p.relative_to(root))
                except Exception:
                    rel=str(p)

                out.append((rel,tuple(sorted(hits))))

    return tuple(sorted(out))

def audit_learning_activation_topology(root=None):
    r=Path(root or _root())

    p317=r/"qseries_v2"/"oracle_adapters"/"independent"/"oad_317_solana_existing_ocl_learning_handoff.py"

    if not p317.is_file():
        raise RuntimeError("certified OAD-317 boundary missing: "+str(p317))

    oad317=_surface(p317,r)

    history=_matching_modules(
        r,
        (
            "oad_273_*.py",
            "oad_274_*.py",
            "oad_275_*.py",
            "oad_312_*.py",
        ),
    )

    outcomes=_matching_modules(
        r,
        (
            "oad_313_*.py",
            "oad_314_*.py",
            "oad_315_*.py",
            "oad_316_*.py",
            "oad_375_*.py",
            "oad_376_*.py",
        ),
    )

    learners=_matching_modules(
        r,
        (
            "ocl_*.py",
            "*continuous*learn*.py",
            "*learner*.py",
        ),
    )

    # Remove adapter modules from learner list. We need the real learning subsystem.
    learners=tuple(
        x for x in learners
        if "oracle_adapters/independent/" not in x.path.replace("\\","/")
    )

    return LearningActivationTopology(
        oad317=oad317,
        solana_history_modules=history,
        outcome_modules=outcomes,
        learner_modules=learners,
        runtime_state_candidates=_runtime_candidates(r),
        execution_authority=False,
    )
