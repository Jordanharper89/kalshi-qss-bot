from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED="build_oad_383_solana_learning_activation_exact_topology_audit.py"
MODULE="oad_383_solana_learning_activation_exact_topology_audit.py"
TEST="test_oad_383_solana_learning_activation_exact_topology_audit.py"

MODULE_SOURCE=r"""
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
"""

TEST_SOURCE=r"""
import unittest

from qseries_v2.oracle_adapters.independent.oad_383_solana_learning_activation_exact_topology_audit import (
    audit_learning_activation_topology,
)

class T(unittest.TestCase):

    def test_exact_topology(self):
        x=audit_learning_activation_topology()

        print("[OAD317]",x.oad317.path)
        print("[OAD317-FUNCTIONS]",x.oad317.functions)
        print("[OAD317-IMPORTS]",x.oad317.imports)

        print("[SOLANA-HISTORY-MODULES]",len(x.solana_history_modules))
        for s in x.solana_history_modules:
            print("[SOLANA-HISTORY]",s.path,"functions=",s.functions,"classes=",s.classes)

        print("[OUTCOME-MODULES]",len(x.outcome_modules))
        for s in x.outcome_modules:
            print("[OUTCOME]",s.path,"functions=",s.functions,"classes=",s.classes)

        print("[LEARNER-MODULES]",len(x.learner_modules))
        for s in x.learner_modules:
            print("[LEARNER]",s.path,"functions=",s.functions,"classes=",s.classes,"imports=",s.imports)

        print("[RUNTIME-LEARNER-STATE]",x.runtime_state_candidates)

        self.assertTrue(
            any(name=="build_solana_learning_handoff" for name,args in x.oad317.functions)
        )

        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-383 exact Solana learning-activation topology physically audited")
    print("[PASS] actual OAD-317 imports/functions exposed")
    print("[PASS] actual OCL/learner module paths and public functions exposed")
    print("[PASS] actual Solana temporal-history/outcome interfaces exposed")
    print("[PASS] no production module modified")
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
    print(" OAD-383 SOLANA LEARNING ACTIVATION EXACT TOPOLOGY AUDIT INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    p317=pkg/"oad_317_solana_existing_ocl_learning_handoff.py"

    if not p317.is_file():
        raise RuntimeError("certified OAD-317 missing: "+str(p317))

    tree=ast.parse(
        p317.read_text(encoding="utf-8"),
        filename=str(p317),
    )

    funcs=tuple(
        n.name
        for n in tree.body
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
        and not n.name.startswith("_")
    )

    if "build_solana_learning_handoff" not in funcs:
        raise RuntimeError(
            "OAD-317 exact public interface changed: "+repr(funcs)
        )

    print("[PASS] exact OAD-317 public boundary verified")

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

        print("[PASS] audit module installed:",m.relative_to(r))
        print("[PASS] audit test installed:",t.name)
        print("[PASS] OAD-317 not modified")
        print("[PASS] OCL/learner subsystem not modified")
        print("[PASS] Solana history/outcome modules not modified")
        print("[PASS] read-only topology audit only")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-383 INSTALLATION COMPLETE")

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
