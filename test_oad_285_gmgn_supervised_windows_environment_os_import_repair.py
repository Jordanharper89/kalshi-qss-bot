from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAUNCHER = ROOT / "run_oracle_live.py"

class T(unittest.TestCase):
    def test_os_import_present(self):
        src = LAUNCHER.read_text(encoding="utf-8")
        tree = ast.parse(src)
        self.assertTrue(
            any(
                isinstance(node, ast.Import)
                and any(alias.name == "os" for alias in node.names)
                for node in tree.body
            ),
            "run_oracle_live.py uses os.environ/os.name but does not import os",
        )

    def test_gmgn_supervised_environment_boundary_preserved(self):
        src = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn(
            'if name == "run_oad_284_gmgn_continuous_intelligence_production_child.py":',
            src,
        )
        self.assertIn("env=os.environ.copy()", src)
        self.assertIn('env["COMSPEC"]', src)
        self.assertIn('env["SystemRoot"]', src)
        self.assertIn('env["APPDATA"]', src)
        self.assertIn('env["USERPROFILE"]', src)
        self.assertIn('env["PATH"]', src)

    def test_truthful_health_boundary_preserved(self):
        src = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("gmgn_checkpoint_cycle_at_spawn", src)
        self.assertIn("restart_backoff_seconds", src)
        self.assertNotIn("execution_authority=TRUE", src)

    def test_launcher_check(self):
        p = subprocess.run(
            [sys.executable, str(LAUNCHER), "--check"],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
        self.assertEqual(p.returncode, 0, msg=p.stdout + "\n" + p.stderr)
        self.assertIn("[READY] Oracle Live Runtime", p.stdout)

if __name__ == "__main__":
    print("=" * 108)
    print(" OAD-285 GMGN SUPERVISED WINDOWS ENVIRONMENT — OS IMPORT REPAIR CERTIFICATION")
    print("=" * 108)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] run_oracle_live.py imports os")
    print("[PASS] GMGN supervised Windows environment boundary preserved")
    print("[PASS] truthful GMGN health supervision preserved")
    print("[PASS] launcher --check passed")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-285 OS IMPORT REPAIR CERTIFIED")
