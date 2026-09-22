from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_052_startup_readiness.py"
TEST = ROOT / "test_ois_052_runtime_startup_dependency_readiness_gate.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_052_BUILD_ID="OIS-052"\nOIS_052_REVISION="OIS_052_RUNTIME_STARTUP_DEPENDENCY_READINESS_GATE_V1"\n\nREQUIRED_SERVICES=("live_shadow","postgresql","observation_intelligence","umd","oml","ocl","osr","ois")\n\n@dataclass(frozen=True)\nclass StartupDependencyState:\n    service_id:str\n    ready:bool\n    certified:bool\n\n@dataclass(frozen=True)\nclass StartupReadinessDecision:\n    required_services:tuple[str,...]\n    missing_or_unready:tuple[str,...]\n    permitted_to_run:bool\n\ndef evaluate_startup_readiness(states):\n    rows={x.service_id:x for x in states}\n    missing=[]\n    for service in REQUIRED_SERVICES:\n        x=rows.get(service)\n        if x is None or not x.ready or not x.certified:\n            missing.append(service)\n    return StartupReadinessDecision(REQUIRED_SERVICES,tuple(missing),not missing)\n\ndef verify_ois_052_runtime_startup_dependency_readiness_gate():\n    states=tuple(StartupDependencyState(x,True,True) for x in REQUIRED_SERVICES)\n    d=evaluate_startup_readiness(states)\n    return d.permitted_to_run and not d.missing_or_unready and len(d.required_services)==8\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_052_startup_readiness import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_052_runtime_startup_dependency_readiness_gate())\n\n    def test_missing_blocks(self):\n        states=tuple(StartupDependencyState(x,True,True) for x in REQUIRED_SERVICES[:-1])\n        self.assertFalse(evaluate_startup_readiness(states).permitted_to_run)\n\n    def test_uncertified_blocks(self):\n        states=[StartupDependencyState(x,True,True) for x in REQUIRED_SERVICES]\n        states[-1]=StartupDependencyState("ois",True,False)\n        self.assertIn("ois",evaluate_startup_readiness(states).missing_or_unready)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-052 CERTIFICATION TEST");print(" RUNTIME STARTUP DEPENDENCY + READINESS GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle startup dependency/readiness gate certified")\n    print("[DONE] OIS-052 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_051_runtime_launcher_contract")
    if getattr(upstream, "verify_ois_051_oracle_live_runtime_production_launcher_contract")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_052_startup_readiness import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-052 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-052 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
