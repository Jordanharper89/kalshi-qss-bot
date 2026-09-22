from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_021_unified_runtime.py"
TEST = ROOT / "test_ois_021_unified_oracle_runtime_composition.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_021_BUILD_ID="OIS-021"\nOIS_021_REVISION="OIS_021_UNIFIED_ORACLE_RUNTIME_COMPOSITION_V1"\n\n@dataclass(frozen=True)\nclass RuntimeComponent:\n    name:str\n    role:str\n    read_only_upstream:bool\n\n@dataclass(frozen=True)\nclass UnifiedOracleRuntimeGraph:\n    components:tuple[RuntimeComponent,...]\n    terminal_dependency:bool\n    execution_authority:bool\n\ndef build_unified_oracle_runtime_graph():\n    names=(\n        ("live_shadow","continuous_market_observation",True),\n        ("postgresql","durable_state_and_history",False),\n        ("observation_intelligence","observation_processing",True),\n        ("umd","market_universe_and_identity",True),\n        ("oml","oracle_memory",True),\n        ("ocl","continuous_learning",True),\n        ("osr","scientific_reasoning",True),\n        ("ois","canonical_intelligence_state",False),\n    )\n    return UnifiedOracleRuntimeGraph(tuple(RuntimeComponent(*x) for x in names),False,False)\n\ndef verify_ois_021_unified_oracle_runtime_composition():\n    g=build_unified_oracle_runtime_graph()\n    return (\n        len(g.components)==8\n        and not g.terminal_dependency\n        and not g.execution_authority\n        and {x.name for x in g.components}=={"live_shadow","postgresql","observation_intelligence","umd","oml","ocl","osr","ois"}\n    )\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_021_unified_runtime import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ois_021_unified_oracle_runtime_composition())\n    def test_no_terminal_dependency(self): self.assertFalse(build_unified_oracle_runtime_graph().terminal_dependency)\n    def test_no_execution(self): self.assertFalse(build_unified_oracle_runtime_graph().execution_authority)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-021 CERTIFICATION TEST");print(" UNIFIED ORACLE RUNTIME COMPOSITION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Unified 24/7 Oracle Runtime composition certified")\n    print("[DONE] OIS-021 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_020_intake_serving_gate")
    if getattr(upstream, "verify_ois_020_continuous_intake_serving_capability_gate")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_021_unified_runtime import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-021 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-021 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
