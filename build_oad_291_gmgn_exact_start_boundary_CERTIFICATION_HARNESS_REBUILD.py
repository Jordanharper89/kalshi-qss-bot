from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path

EXPECTED = "build_oad_291_gmgn_exact_start_boundary_CERTIFICATION_HARNESS_REBUILD.py"
LAUNCHER = "run_oracle_live.py"
TEST = "test_oad_291_gmgn_supervised_node_path_exact_start_boundary.py"

TEST_SOURCE = r"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path.cwd().resolve()
LAUNCHER = ROOT / "run_oracle_live.py"
RUNNER = ROOT / "run_oad_290_gmgn_clean_continuous_intelligence_child.py"


def load_launcher():
    name = "oracle_live_env_test"
    spec = importlib.util.spec_from_file_location(name, LAUNCHER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to create launcher import spec")
    mod = importlib.util.module_from_spec(spec)

    # Python 3.14 dataclasses resolves the module through sys.modules
    # while decorating classes during exec_module().
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


class DummyProc:
    def poll(self):
        return None


class T(unittest.TestCase):
    def test_01_exact_binding_and_truthful_health_preserved(self):
        s = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn(
            '"gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py"',
            s,
        )
        self.assertIn("gmgn_checkpoint_cycle_at_spawn", s)
        self.assertIn("if cp.last_error:", s)
        self.assertIn("if success_age > 240.0:", s)
        self.assertIn("restart_backoff_seconds", s)
        self.assertNotIn("execution_authority=TRUE", s)

    def test_02_gmgn_only_supervised_environment_contains_node_and_npm(self):
        mod = load_launcher()
        captured = {}

        def fake_popen(args, **kwargs):
            captured["args"] = args
            captured.update(kwargs)
            return DummyProc()

        with patch.object(mod.subprocess, "Popen", side_effect=fake_popen):
            mod._start(ROOT, RUNNER.name)

        env = captured.get("env")
        self.assertIsInstance(env, dict)
        self.assertIn("GMGN_SUPERVISED_NODE_EXE", env)
        self.assertIn("GMGN_SUPERVISED_CLI", env)

        node = Path(env["GMGN_SUPERVISED_NODE_EXE"])
        gmgn = Path(env["GMGN_SUPERVISED_CLI"])

        self.assertTrue(node.is_file(), node)
        self.assertTrue(gmgn.is_file(), gmgn)

        path_parts = [
            os.path.normcase(os.path.normpath(x))
            for x in env["PATH"].split(os.pathsep)
        ]
        self.assertIn(
            os.path.normcase(os.path.normpath(str(node.parent))),
            path_parts,
        )
        self.assertIn(
            os.path.normcase(os.path.normpath(str(gmgn.parent))),
            path_parts,
        )

        n = subprocess.run(
            [str(node), "--version"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        print("[SUPERVISED NODE]", node)
        print("[SUPERVISED NODE VERSION]", n.stdout.strip())
        if n.stderr:
            print(n.stderr, end="")
        self.assertEqual(n.returncode, 0)

        comspec = env.get("COMSPEC")
        self.assertTrue(comspec)

        g = subprocess.run(
            [
                comspec,
                "/d",
                "/s",
                "/c",
                subprocess.list2cmdline([str(gmgn), "--version"]),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
        print("[SUPERVISED GMGN]", gmgn)
        print("[SUPERVISED GMGN VERSION]", g.stdout.strip())
        if g.stderr:
            print(g.stderr, end="")
        self.assertEqual(g.returncode, 0)

        c = subprocess.run(
            [
                comspec,
                "/d",
                "/s",
                "/c",
                subprocess.list2cmdline([str(gmgn), "config", "--check"]),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        print("[SUPERVISED CONFIG CHECK RETURN]", c.returncode)
        if c.stdout:
            print(c.stdout, end="")
        if c.stderr:
            print(c.stderr, end="")
        self.assertEqual(c.returncode, 0)

    def test_03_non_gmgn_child_spawn_has_no_special_env(self):
        mod = load_launcher()
        other = None
        for key, name in mod.CHILDREN.items():
            if key != "gmgn_intelligence":
                other = name
                break
        self.assertIsNotNone(other)

        captured = {}

        def fake_popen(args, **kwargs):
            captured["args"] = args
            captured.update(kwargs)
            return DummyProc()

        with patch.object(mod.subprocess, "Popen", side_effect=fake_popen):
            mod._start(ROOT, other)

        self.assertNotIn("env", captured)

    def test_04_physical_oad290_cycle_under_exact_supervised_env(self):
        mod = load_launcher()
        captured = {}

        def fake_popen(args, **kwargs):
            captured.update(kwargs)
            return DummyProc()

        with patch.object(mod.subprocess, "Popen", side_effect=fake_popen):
            mod._start(ROOT, RUNNER.name)

        env = captured["env"]

        p = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--max-cycles",
                "1",
                "--cadence-seconds",
                "1",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=240,
            check=False,
        )
        print(p.stdout, end="")
        if p.stderr:
            print(p.stderr, end="")

        self.assertEqual(p.returncode, 0)
        self.assertIn("status=SUCCESS", p.stdout)
        self.assertIn("exact_readback=3", p.stdout)
        self.assertIn("execution_authority=FALSE", p.stdout)

    def test_05_launcher_check(self):
        p = subprocess.run(
            [sys.executable, str(LAUNCHER), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        print(p.stdout, end="")
        if p.stderr:
            print(p.stderr, end="")
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    print("=" * 116)
    print(" OAD-291 GMGN SUPERVISED NODE PATH — EXACT _start BOUNDARY CERTIFICATION")
    print("=" * 116)

    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] exact OAD-290 GMGN child binding preserved")
    print("[PASS] supervised Node executable physically verified")
    print("[PASS] supervised gmgn-cli admission physically verified")
    print("[PASS] exact GMGN-only PATH includes Node + npm")
    print("[PASS] non-GMGN child spawn behavior preserved")
    print("[PASS] OAD-290 physical cycle succeeded under exact supervised environment")
    print("[PASS] exact_readback=3")
    print("[PASS] truthful provider health preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-291 EXACT START-BOUNDARY NODE PATH REBUILD CERTIFIED")
"""


def root():
    for b in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (b, *b.parents):
            if (p / "qseries_v2").is_dir() and (p / LAUNCHER).is_file():
                return p
    raise RuntimeError("Q Series repository root not found")


def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename identity mismatch")

    r = root()
    launcher = r / LAUNCHER
    test = r / TEST

    print("=" * 116)
    print(" OAD-291 GMGN EXACT _start BOUNDARY — CERTIFICATION HARNESS REBUILD")
    print("=" * 116)
    print("[ROOT]", r)

    source = launcher.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        'def _start(root,name):',
        '"gmgn_intelligence": "run_oad_290_gmgn_clean_continuous_intelligence_child.py"',
        'GMGN_SUPERVISED_NODE_EXE',
        'GMGN_SUPERVISED_CLI',
        'gmgn_checkpoint_cycle_at_spawn',
        'if cp.last_error:',
        'if success_age > 240.0:',
        'restart_backoff_seconds',
        'execution_authority=FALSE',
    )
    for marker in required:
        if marker not in source:
            raise RuntimeError("installed production boundary missing: " + marker)

    if "execution_authority=TRUE" in source:
        raise RuntimeError("execution safety boundary violation")

    q = subprocess.run(
        [sys.executable, str(launcher), "--check"],
        cwd=r,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if q.returncode != 0:
        raise RuntimeError("launcher --check failed:\n" + q.stdout + "\n" + q.stderr)

    old = test.read_bytes() if test.exists() else None
    try:
        ts = textwrap.dedent(TEST_SOURCE).lstrip()
        ast.parse(ts, filename=str(test))
        test.write_text(ts, encoding="utf-8", newline="\n")

        print("[PASS] installed OAD-291 production launcher boundary verified")
        print("[PASS] previous failure classified as Python 3.14 test-loader defect")
        print("[PASS] production run_oracle_live.py left unchanged")
        print("[PASS] certification loader now registers module in sys.modules before exec_module")
        print("[PASS] physical Node/gmgn/OAD-290 certification retained")
        print("[PASS] launcher --check passed")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OAD-291 CERTIFICATION HARNESS REBUILD INSTALLED")

    except Exception:
        if old is None:
            if test.exists():
                test.unlink()
        else:
            test.write_bytes(old)
        print("[ROLLBACK] certification test restored")
        raise


if __name__ == "__main__":
    main()
