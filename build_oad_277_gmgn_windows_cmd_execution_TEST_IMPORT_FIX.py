from __future__ import annotations

import ast
import hashlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path

BUILD_ID = "OAD-277"
REVISION = "OAD_277_GMGN_WINDOWS_CMD_EXECUTION_PRODUCTION_BOUNDARY_REBUILD_V1"
TITLE = "GMGN WINDOWS CMD EXECUTION PRODUCTION BOUNDARY REBUILD"
EXPECTED_FILENAME = "build_oad_277_gmgn_windows_cmd_execution_TEST_IMPORT_FIX.py"

MODULE_REL = Path("qseries_v2/oracle_adapters/independent/oad_277_gmgn_production_admission_boundary.py")
TEST_REL = Path("test_oad_277_gmgn_production_admission_boundary.py")

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False


@dataclass(frozen=True, slots=True)
class GMGNAdmission:
    cli_path: str | None
    api_key_present: bool
    version_ok: bool
    admitted: bool
    execution_authority: bool = False


def _candidate_cli_paths():
    candidates = []

    for name in ("gmgn-cli", "gmgn-cli.cmd"):
        resolved = shutil.which(name)
        if resolved:
            candidates.append(Path(resolved))

    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "").strip()
        if appdata:
            npm_dir = Path(appdata) / "npm"
            candidates.extend((npm_dir / "gmgn-cli.cmd", npm_dir / "gmgn-cli"))

        userprofile = os.environ.get("USERPROFILE", "").strip()
        if userprofile:
            npm_dir = Path(userprofile) / "AppData" / "Roaming" / "npm"
            candidates.extend((npm_dir / "gmgn-cli.cmd", npm_dir / "gmgn-cli"))

    seen = set()
    for candidate in candidates:
        try:
            normalized = str(candidate.expanduser().resolve())
        except Exception:
            normalized = str(candidate)
        key = os.path.normcase(os.path.normpath(normalized))
        if key in seen:
            continue
        seen.add(key)
        yield Path(normalized)


def locate_gmgn_cli():
    for candidate in _candidate_cli_paths():
        if candidate.is_file():
            return str(candidate)
    return None


def _windows_cmd_command(cli_path, args):
    comspec = os.environ.get("COMSPEC", "").strip()
    if not comspec:
        system_root = os.environ.get("SystemRoot", r"C:\Windows").strip() or r"C:\Windows"
        comspec = str(Path(system_root) / "System32" / "cmd.exe")

    # npm global executables on Windows are .cmd shims.  CreateProcess cannot
    # be relied upon to execute those shims identically from every supervised
    # Python child environment, so invoke the shim through cmd.exe explicitly.
    command_text = subprocess.list2cmdline([str(cli_path), *[str(x) for x in args]])
    return [comspec, "/d", "/s", "/c", command_text]


def _run_cli(cli_path, args, timeout_seconds):
    cli_path = str(cli_path)
    suffix = Path(cli_path).suffix.lower()

    if os.name == "nt" and suffix in (".cmd", ".bat"):
        command = _windows_cmd_command(cli_path, args)
    else:
        command = [cli_path, *[str(x) for x in args]]

    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=float(timeout_seconds),
        check=False,
    )


def _gmgn_config_check(cli_path, timeout_seconds):
    if not cli_path:
        return False
    try:
        p = _run_cli(cli_path, ["config", "--check"], timeout_seconds)
        return p.returncode == 0
    except Exception:
        return False


def _gmgn_version_check(cli_path, timeout_seconds):
    if not cli_path:
        return False
    try:
        p = _run_cli(cli_path, ["--version"], timeout_seconds)
        return p.returncode == 0 and bool((p.stdout or p.stderr or "").strip())
    except Exception:
        return False


def evaluate_gmgn_admission(timeout_seconds=10.0):
    cli = locate_gmgn_cli()
    config_ok = _gmgn_config_check(cli, timeout_seconds)
    version_ok = _gmgn_version_check(cli, timeout_seconds)
    key_present = bool(config_ok)
    admitted = bool(cli and key_present and version_ok)

    return GMGNAdmission(
        cli_path=cli,
        api_key_present=key_present,
        version_ok=version_ok,
        admitted=admitted,
        execution_authority=False,
    )


def require_gmgn_admission(timeout_seconds=10.0):
    a = evaluate_gmgn_admission(timeout_seconds)

    if not a.cli_path:
        raise RuntimeError(
            "GMGN_NOT_ADMITTED: gmgn-cli not found by PATH or deterministic Windows npm discovery"
        )
    if not a.version_ok:
        raise RuntimeError("GMGN_NOT_ADMITTED: gmgn-cli version check failed")
    if not a.api_key_present:
        raise RuntimeError(
            "GMGN_NOT_ADMITTED: gmgn-cli config --check did not confirm configured credentials"
        )
    if not a.admitted:
        raise RuntimeError("GMGN_NOT_ADMITTED: production admission gate is closed")

    return a
"""

TEST_SOURCE = r"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import qseries_v2.oracle_adapters.independent.oad_277_gmgn_production_admission_boundary as M


class T(unittest.TestCase):
    def test_windows_npm_fallback_without_path(self):
        with tempfile.TemporaryDirectory() as td:
            profile = Path(td)
            cli = profile / "AppData" / "Roaming" / "npm" / "gmgn-cli.cmd"
            cli.parent.mkdir(parents=True, exist_ok=True)
            cli.write_text("@echo off\r\n", encoding="utf-8")

            env = dict(os.environ)
            env["USERPROFILE"] = str(profile)
            env.pop("APPDATA", None)

            with patch.dict(os.environ, env, clear=True):
                with patch.object(M.shutil, "which", return_value=None):
                    with patch.object(M.os, "name", "nt"):
                        found = M.locate_gmgn_cli()

            self.assertIsNotNone(found)
            self.assertEqual(
                os.path.normcase(os.path.normpath(found)),
                os.path.normcase(os.path.normpath(str(cli.resolve()))),
            )

    def test_windows_cmd_shim_is_executed_through_comspec(self):
        fake_cli = r"C:\Users\test\AppData\Roaming\npm\gmgn-cli.cmd"
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="1.6.0\n", stderr="")

        with patch.dict(os.environ, {"COMSPEC": r"C:\Windows\System32\cmd.exe"}, clear=False):
            with patch.object(M.os, "name", "nt"):
                with patch.object(M.subprocess, "run", return_value=completed) as run:
                    p = M._run_cli(fake_cli, ["--version"], 10.0)

        self.assertEqual(p.returncode, 0)
        command = run.call_args.args[0]
        self.assertEqual(command[0], r"C:\Windows\System32\cmd.exe")
        self.assertEqual(command[1:4], ["/d", "/s", "/c"])
        self.assertIn("gmgn-cli.cmd", command[4])
        self.assertIn("--version", command[4])

    def test_non_cmd_cli_keeps_direct_execution(self):
        fake_cli = r"C:\tools\gmgn-cli.exe"
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="1.6.0\n", stderr="")
        with patch.object(M.subprocess, "run", return_value=completed) as run:
            M._run_cli(fake_cli, ["--version"], 10.0)
        self.assertEqual(run.call_args.args[0], [fake_cli, "--version"])

    def test_admission_contract_and_safety(self):
        fake = M.GMGNAdmission(
            cli_path=r"C:\Users\test\AppData\Roaming\npm\gmgn-cli.cmd",
            api_key_present=True,
            version_ok=True,
            admitted=True,
            execution_authority=False,
        )
        with patch.object(M, "evaluate_gmgn_admission", return_value=fake):
            required = M.require_gmgn_admission()
        self.assertTrue(required.admitted)
        self.assertFalse(required.execution_authority)
        self.assertFalse(M.PROBABILITY_ENABLED)
        self.assertFalse(M.DIRECTION_ENABLED)
        self.assertFalse(M.PUBLICATION_ALLOWED)
        self.assertFalse(M.EXECUTION_AUTHORITY)

    def test_physical_admission(self):
        a = M.evaluate_gmgn_admission()
        print("[GMGN] cli_path=", a.cli_path)
        print("[GMGN] config_check_ok=", a.api_key_present)
        print("[GMGN] version_ok=", a.version_ok)
        print("[GMGN] admitted=", a.admitted)

        self.assertIsNotNone(a.cli_path, "gmgn-cli was not found")
        self.assertTrue(a.version_ok, "gmgn-cli --version failed through production execution boundary")
        self.assertTrue(
            a.api_key_present,
            "gmgn-cli config --check did not confirm configured credentials",
        )
        self.assertTrue(a.admitted, "GMGN production admission gate did not open")
        self.assertFalse(a.execution_authority)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-277 GMGN WINDOWS CMD EXECUTION PRODUCTION BOUNDARY CERTIFICATION")
    print("=" * 120)
    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] deterministic Windows npm discovery preserved")
    print("[PASS] Windows .cmd/.bat shims execute through COMSPEC")
    print("[PASS] direct executable invocation preserved")
    print("[PASS] gmgn-cli --version physically verified")
    print("[PASS] gmgn-cli config --check physically verified")
    print("[PASS] GMGN production admission OPEN")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-277 WINDOWS CMD EXECUTION PRODUCTION BOUNDARY CERTIFIED")
"""


def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")


def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch: expected " + EXPECTED_FILENAME)

    root = locate_root()
    module = root / MODULE_REL
    test = root / TEST_REL

    print("=" * 120)
    print(" " + BUILD_ID + " " + TITLE + " INSTALLER")
    print("=" * 120)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", root)

    if not module.is_file():
        raise RuntimeError("Exact OAD-277 production module missing: " + str(MODULE_REL))

    current = module.read_text(encoding="utf-8")
    required_current = (
        "class GMGNAdmission",
        "def _candidate_cli_paths",
        "def locate_gmgn_cli",
        "def _run_cli",
        "def _gmgn_config_check",
        "def _gmgn_version_check",
        "def evaluate_gmgn_admission",
        "def require_gmgn_admission",
        'Path(userprofile) / "AppData" / "Roaming" / "npm"',
        '["config", "--check"]',
        '["--version"]',
    )
    for marker in required_current:
        if marker not in current:
            raise RuntimeError("Current repaired OAD-277 contract marker missing: " + marker)
    print("[PASS] exact current OAD-277 Windows discovery boundary verified")

    protected = []
    for rel, label in (
        (
            Path("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py"),
            "Frozen OPH-023",
        ),
        (
            Path("qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py"),
            "Frozen Kalshi OAD-055",
        ),
    ):
        p = root / rel
        if not p.is_file():
            raise RuntimeError(label + " missing: " + str(rel))
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))
        print("[PASS]", label, "verified")

    old_module = module.read_bytes()
    old_test = test.read_bytes() if test.exists() else None

    try:
        normalized_module = textwrap.dedent(MODULE_SOURCE).lstrip()
        normalized_test = textwrap.dedent(TEST_SOURCE).lstrip()
        ast.parse(normalized_module, filename=str(module))
        ast.parse(normalized_test, filename=str(test))

        module.write_text(normalized_module, encoding="utf-8", newline="\n")
        test.write_text(normalized_test, encoding="utf-8", newline="\n")

        for p, expected in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise RuntimeError("Frozen boundary changed: " + p.name)

        installed = module.read_text(encoding="utf-8")
        for marker in (
            "def _windows_cmd_command",
            'os.environ.get("COMSPEC"',
            '"/d", "/s", "/c"',
            "subprocess.list2cmdline",
            "def _run_cli",
            "def evaluate_gmgn_admission",
            "def require_gmgn_admission",
        ):
            if marker not in installed:
                raise RuntimeError("Rebuilt OAD-277 execution marker missing: " + marker)

        # Run the test.  On the user's Windows production host this includes
        # the real physical CLI admission test.  Any failure rolls back.
        proc = subprocess.run(
            [sys.executable, str(test)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "OAD-277 certification failed:\n" + proc.stdout + "\n" + proc.stderr
            )

        print("[PASS] OAD-277 repaired in place; no corrective OAD layer added")
        print("[PASS] deterministic Windows npm CLI discovery preserved")
        print("[PASS] Windows npm .cmd execution repaired through COMSPEC")
        print("[PASS] exact CLI path remains production execution target")
        print("[PASS] gmgn-cli --version physically verified by certification test")
        print("[PASS] gmgn-cli config --check physically verified by certification test")
        print("[PASS] downstream GMGNAdmission public contract preserved")
        print("[PASS] frozen OPH-023 and Kalshi OAD-055 unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-277 WINDOWS CMD EXECUTION PRODUCTION BOUNDARY REBUILD INSTALLED")

    except Exception:
        module.write_bytes(old_module)
        if old_test is None:
            if test.exists():
                test.unlink()
        else:
            test.write_bytes(old_test)
        print("[ROLLBACK] OAD-277 module/test restored")
        raise


if __name__ == "__main__":
    main()
