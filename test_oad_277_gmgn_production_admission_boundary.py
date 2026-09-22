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
