from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_208_CRYPTO_LEARNING_PHYSICAL_LAUNCHER_ADMISSION_GATE_V1"

MODULE_SOURCE=r"""
from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path

EXPECTED_CORE=frozenset({
    "fast_lane","inventory","reasoning","learning",
    "coverage","canonical_writer","continuity",
})
CRYPTO_CHILD="crypto_learning"
CRYPTO_RUNNER="run_oad_207_crypto_continuous_learning_production_child.py"

@dataclass(frozen=True,slots=True)
class CryptoLearningLauncherAdmission:
    launcher_present:bool
    expected_core_present:bool
    truthful_health_present:bool
    crypto_runner_present:bool
    crypto_child_already_present:bool
    execution_boundary_preserved:bool
    admitted:bool

def read_children(source):
    tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and isinstance(node.value,ast.Dict) and any(
            isinstance(t,ast.Name) and t.id=="CHILDREN" for t in node.targets
        ):
            out={}
            for k,v in zip(node.value.keys,node.value.values):
                if isinstance(k,ast.Constant) and isinstance(v,ast.Constant) and isinstance(v.value,str):
                    out[str(k.value)]=str(v.value)
            return out
    raise RuntimeError("Physical run_oracle_LIVE.py CHILDREN dictionary not found")

def evaluate_crypto_learning_launcher_admission(root=None):
    root=Path(root or Path.cwd()).resolve()
    launcher=root/"run_oracle_LIVE.py"
    runner=root/CRYPTO_RUNNER
    if not launcher.is_file():
        return CryptoLearningLauncherAdmission(False,False,False,runner.is_file(),False,False,False)
    source=launcher.read_text(encoding="utf-8")
    ast.parse(source)
    children=read_children(source)
    core=EXPECTED_CORE.issubset(children)
    truthful=all(x in source for x in (
        "STARTING","HEALTHY","DEGRADED","FAILED",
        "recent_restarts_60s","restart_backoff_seconds",
    ))
    exec_ok="execution_authority=TRUE" not in source
    already=children.get(CRYPTO_CHILD)==CRYPTO_RUNNER
    admitted=bool(core and truthful and runner.is_file() and exec_ok)
    return CryptoLearningLauncherAdmission(
        True,core,truthful,runner.is_file(),already,exec_ok,admitted
    )
"""

TEST_SOURCE=r"""
import unittest
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_208_crypto_learning_physical_launcher_admission_gate import evaluate_crypto_learning_launcher_admission
class T(unittest.TestCase):
    def test_physical(self):
        r=evaluate_crypto_learning_launcher_admission(Path.cwd())
        print("[LAUNCHER]",r.launcher_present)
        print("[CORE]",r.expected_core_present)
        print("[TRUTHFUL_HEALTH]",r.truthful_health_present)
        print("[RUNNER]",r.crypto_runner_present)
        print("[ALREADY_PRESENT]",r.crypto_child_already_present)
        print("[ADMITTED]",r.admitted)
        self.assertTrue(r.admitted)
        self.assertTrue(r.execution_boundary_preserved)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-208 physical Oracle launcher admission gate certified")
"""

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2/oracle_adapters/independent"
    if not (r/"run_oracle_LIVE.py").is_file(): raise RuntimeError("Physical run_oracle_LIVE.py missing")
    if not (r/"run_oad_207_crypto_continuous_learning_production_child.py").is_file(): raise RuntimeError("OAD-207 runner missing")
    mod=pkg/"oad_208_crypto_learning_physical_launcher_admission_gate.py"
    test=r/"test_oad_208_crypto_learning_physical_launcher_admission_gate.py"
    old={p:(p.read_bytes() if p.exists() else None) for p in (mod,test)}
    try:
        write(mod,MODULE_SOURCE); write(test,TEST_SOURCE)
        print("[PASS] physical launcher admission module installed")
        print("[PASS] installer refuses missing launcher/core/ORH truthful-health contract")
        print("[DONE] OAD-208 INSTALLATION COMPLETE")
    except Exception:
        for p,d in old.items():
            if d is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(d)
        raise
if __name__=="__main__":main()
