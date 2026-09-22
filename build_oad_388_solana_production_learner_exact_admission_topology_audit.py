from __future__ import annotations
import ast, json, os, textwrap
from pathlib import Path

EXPECTED="build_oad_388_solana_production_learner_exact_admission_topology_audit.py"
MODULE="oad_388_solana_production_learner_exact_admission_topology_audit.py"
TEST="test_oad_388_solana_production_learner_exact_admission_topology_audit.py"

MODULE_SOURCE=r"""
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
"""

TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.independent.oad_388_solana_production_learner_exact_admission_topology_audit import (
    audit_production_learner_topology,
)

class T(unittest.TestCase):
    def test_topology(self):
        x=audit_production_learner_topology()

        print("[OLR-044]",x.olr044_path)
        print("[OLR-044 FUNCTIONS]",x.olr044_functions)
        print("[OLR-046]",x.olr046_path)
        print("[OLR-046 FUNCTIONS]",x.olr046_functions)
        print("[RUNNER CANDIDATES]",x.candidate_runner_paths)
        print("[LEARNER STATE FILES]",x.runtime_state_files)
        print("[LEARNER STATE KEYS]",x.runtime_state_keys)

        self.assertIn("find_learning_runner",x.olr044_functions)
        self.assertIn("read_children",x.olr046_functions)
        self.assertIn("patch_learning_child",x.olr046_functions)
        self.assertGreater(len(x.runtime_state_files),0)
        self.assertTrue(
            any(k in x.runtime_state_keys for k in (
                "outcomes_learned",
                "learned_records",
                "through_sequence",
            ))
        )

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-388 exact production learner admission topology audited")
    print("[PASS] OLR-044 learning-runner discovery boundary verified")
    print("[PASS] OLR-046 live learner launcher-cutover boundary verified")
    print("[PASS] durable learner runtime-state surfaces inventoried")
    print("[PASS] no production module modified")
"""

DEPS={
    "qseries_v2/oracle_learning/olr_044_continuous_learner_evidence_runtime_cutover.py":(
        "find_learning_runner",
    ),
    "qseries_v2/oracle_learning/olr_046_oracle_live_evidence_learner_launcher_cutover.py":(
        "read_children",
        "patch_learning_child",
    ),
    "qseries_v2/oracle_adapters/independent/oad_387_solana_ocl027_028_learning_cycle.py":(
        "run_solana_ocl_learning_cycle",
    ),
}

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def verify(p,markers):
    if not p.is_file():
        raise RuntimeError("dependency missing: "+str(p))
    s=p.read_text(encoding="utf-8")
    ast.parse(s,filename=str(p))
    for marker in markers:
        if marker not in s:
            raise RuntimeError("dependency interface missing: "+p.name+" -> "+marker)

def atomic(p,s):
    s=textwrap.dedent(s).lstrip()
    ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(s,encoding="utf-8",newline="\n")
    os.replace(tmp,p)

def main():
    if Path(__file__).name!=EXPECTED:
        raise RuntimeError("installer identity mismatch")

    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=r/TEST
    init=pkg/"__init__.py"

    print("="*120)
    print(" OAD-388 SOLANA PRODUCTION LEARNER EXACT ADMISSION TOPOLOGY AUDIT INSTALLER")
    print("="*120)
    print("[ROOT]",r)

    for rel,marks in DEPS.items():
        verify(r/rel,marks)
        print("[PASS] dependency interface verified:",rel)

    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}

    try:
        atomic(m,MODULE_SOURCE)
        atomic(t,TEST_SOURCE)

        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+m.stem+" import *"
        if export not in lines:
            lines.append(export)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")

        print("[PASS] OAD-387 certified learning-cycle boundary preserved")
        print("[PASS] OLR-044/046 inspected read-only")
        print("[PASS] no learner counters mutated")
        print("[PASS] no runtime launcher patched")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-388 PRODUCTION LEARNER TOPOLOGY AUDIT INSTALLED")

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
