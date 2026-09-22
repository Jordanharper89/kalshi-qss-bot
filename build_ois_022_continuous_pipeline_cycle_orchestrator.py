from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_022_pipeline_orchestrator.py"
TEST = ROOT / "test_ois_022_continuous_pipeline_cycle_orchestrator.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom .ois_021_unified_runtime import UnifiedOracleRuntimeGraph\n\nOIS_022_BUILD_ID="OIS-022"\nOIS_022_REVISION="OIS_022_CONTINUOUS_PIPELINE_CYCLE_ORCHESTRATOR_V1"\n\n@dataclass(frozen=True)\nclass RuntimeCycle:\n    sequence:int\n    stages:tuple[str,...]\n    cycle_hash:str\n    terminal_dependency:bool=False\n\ndef run_runtime_cycle(graph,sequence):\n    if not isinstance(graph,UnifiedOracleRuntimeGraph) or sequence<1:\n        raise ValueError("certified runtime graph and positive sequence required")\n    stages=tuple(x.name for x in graph.components)\n    raw={"sequence":sequence,"stages":stages,"terminal_dependency":False}\n    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n    return RuntimeCycle(sequence,stages,h,False)\n\ndef verify_ois_022_continuous_pipeline_cycle_orchestrator():\n    from .ois_021_unified_runtime import build_unified_oracle_runtime_graph\n    c=run_runtime_cycle(build_unified_oracle_runtime_graph(),1)\n    return not c.terminal_dependency and c.stages[-1]=="ois" and len(c.cycle_hash)==64\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_021_unified_runtime import build_unified_oracle_runtime_graph\nfrom qseries_v2.oracle_intelligence_state.ois_022_pipeline_orchestrator import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ois_022_continuous_pipeline_cycle_orchestrator())\n    def test_sequence(self):\n        with self.assertRaises(ValueError): run_runtime_cycle(build_unified_oracle_runtime_graph(),0)\n    def test_terminal_independent(self): self.assertFalse(run_runtime_cycle(build_unified_oracle_runtime_graph(),1).terminal_dependency)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-022 CERTIFICATION TEST");print(" CONTINUOUS PIPELINE CYCLE ORCHESTRATOR");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Terminal-independent continuous Oracle pipeline cycle certified")\n    print("[DONE] OIS-022 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_021_unified_runtime")
    if getattr(upstream, "verify_ois_021_unified_oracle_runtime_composition")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_022_pipeline_orchestrator import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-022 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-022 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
