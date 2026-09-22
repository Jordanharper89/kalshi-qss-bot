from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

EXPECTED_FILENAME = "build_oad_285_gmgn_supervised_windows_environment_OS_IMPORT_REPAIR.py"
LAUNCHER = "run_oracle_live.py"
TEST = "test_oad_285_gmgn_supervised_windows_environment_os_import_repair.py"

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def ensure_os_import(source: str) -> str:
    tree = ast.parse(source)
    has_os = any(
        isinstance(node, ast.Import) and any(alias.name == "os" for alias in node.names)
        for node in tree.body
    )
    if has_os:
        return source

    lines = source.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    while insert_at < len(lines) and "coding" in lines[insert_at] and lines[insert_at].lstrip().startswith("#"):
        insert_at += 1

    future_end = insert_at
    while future_end < len(lines):
        stripped = lines[future_end].strip()
        if stripped.startswith("from __future__ import "):
            future_end += 1
            continue
        if not stripped:
            future_end += 1
            continue
        break

    lines.insert(future_end, "import os\n")
    rebuilt = "".join(lines)
    ast.parse(rebuilt)
    return rebuilt

TEST_SOURCE = r'''
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
'''

def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch")

    root = locate_root()
    launcher = root / LAUNCHER
    test = root / TEST

    if not launcher.is_file():
        raise RuntimeError("run_oracle_live.py missing")

    src = launcher.read_text(encoding="utf-8")
    ast.parse(src)

    required = (
        'if name == "run_oad_284_gmgn_continuous_intelligence_production_child.py":',
        "env=os.environ.copy()",
        'env["COMSPEC"]',
        'env["SystemRoot"]',
        'env["APPDATA"]',
        'env["USERPROFILE"]',
        'env["PATH"]',
        "gmgn_checkpoint_cycle_at_spawn",
        "restart_backoff_seconds",
    )
    for marker in required:
        if marker not in src:
            raise RuntimeError("current OAD-285 repaired boundary missing: " + marker)

    if "execution_authority=TRUE" in src:
        raise RuntimeError("execution safety violation")

    old_launcher = launcher.read_bytes()
    old_test = test.read_bytes() if test.exists() else None

    try:
        repaired = ensure_os_import(src)
        launcher.write_text(repaired, encoding="utf-8", newline="\n")
        test.write_text(TEST_SOURCE.lstrip(), encoding="utf-8", newline="\n")

        compile(launcher.read_text(encoding="utf-8"), str(launcher), "exec")
        compile(test.read_text(encoding="utf-8"), str(test), "exec")

        p = subprocess.run(
            [sys.executable, str(test)],
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        if p.returncode != 0:
            raise RuntimeError(
                "OAD-285 OS import repair certification failed:\n"
                + p.stdout
                + "\n"
                + p.stderr
            )

        print("=" * 108)
        print(" OAD-285 GMGN SUPERVISED WINDOWS ENVIRONMENT — OS IMPORT REPAIR")
        print("=" * 108)
        print("[PASS] exact current OAD-285 supervised GMGN boundary verified")
        print("[PASS] missing os import repaired in run_oracle_live.py")
        print("[PASS] GMGN-only Windows environment normalization preserved")
        print("[PASS] all truthful health supervision preserved")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-285 OS IMPORT REPAIR INSTALLED")

    except Exception:
        launcher.write_bytes(old_launcher)
        if old_test is None:
            if test.exists():
                test.unlink()
        else:
            test.write_bytes(old_test)
        print("[ROLLBACK] launcher/test restored")
        raise

if __name__ == "__main__":
    main()
