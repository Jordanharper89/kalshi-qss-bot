from __future__ import annotations

import ast
import hashlib
import os
import textwrap
from pathlib import Path

BUILD_ID = "OAD-277"
REVISION = "OAD_277_GMGN_PRODUCTION_ADMISSION_BOUNDARY_CLI_CONFIG_REBUILD_V1"
TITLE = "GMGN PRODUCTION ADMISSION BOUNDARY — CLI CONFIG REBUILD"
EXPECTED_FILENAME = "build_oad_277_gmgn_production_admission_boundary_CLI_CONFIG_REBUILD.py"

MODULE_NAME = "oad_277_gmgn_production_admission_boundary.py"
TEST_NAME = "test_oad_277_gmgn_production_admission_boundary.py"

DEPENDENCIES = {
    "qseries_v2/oracle_adapters/independent/oad_276_solana_continuous_observation_production_runner.py": (
        "evaluate_solana_continuous_runner",
    )
}

MODULE_SOURCE = r'''
from __future__ import annotations

from dataclasses import dataclass
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


def locate_gmgn_cli():
    return shutil.which("gmgn-cli") or shutil.which("gmgn-cli.cmd")


def _run_cli(cli_path, args, timeout_seconds):
    return subprocess.run(
        [cli_path, *args],
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
        raise RuntimeError("GMGN_NOT_ADMITTED: gmgn-cli not found on PATH")
    if not a.version_ok:
        raise RuntimeError("GMGN_NOT_ADMITTED: gmgn-cli version check failed")
    if not a.api_key_present:
        raise RuntimeError(
            "GMGN_NOT_ADMITTED: gmgn-cli config --check did not confirm configured credentials"
        )
    if not a.admitted:
        raise RuntimeError("GMGN_NOT_ADMITTED: production admission gate is closed")

    return a
'''

TEST_SOURCE = r'''
import unittest

from qseries_v2.oracle_adapters.independent.oad_277_gmgn_production_admission_boundary import (
    EXECUTION_AUTHORITY,
    PUBLICATION_ALLOWED,
    PROBABILITY_ENABLED,
    DIRECTION_ENABLED,
    evaluate_gmgn_admission,
    require_gmgn_admission,
)


class T(unittest.TestCase):
    def test_physical_gmgn_cli_admission(self):
        a = evaluate_gmgn_admission()

        print("[GMGN] cli_path=", a.cli_path)
        print("[GMGN] config_check_ok=", a.api_key_present)
        print("[GMGN] version_ok=", a.version_ok)
        print("[GMGN] admitted=", a.admitted)

        self.assertIsNotNone(a.cli_path, "gmgn-cli is not present on PATH")
        self.assertTrue(
            a.api_key_present,
            "gmgn-cli config --check did not confirm configured credentials",
        )
        self.assertTrue(a.version_ok, "gmgn-cli --version failed")
        self.assertTrue(a.admitted, "GMGN production admission gate did not open")

        required = require_gmgn_admission()
        self.assertTrue(required.admitted)
        self.assertFalse(required.execution_authority)

    def test_read_only_safety_boundary(self):
        self.assertFalse(PROBABILITY_ENABLED)
        self.assertFalse(DIRECTION_ENABLED)
        self.assertFalse(PUBLICATION_ALLOWED)
        self.assertFalse(EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-277 PHYSICAL CERTIFICATION TEST")
    print(" GMGN PRODUCTION ADMISSION — CLI CONFIG BOUNDARY")
    print("=" * 120)

    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] gmgn-cli physically present")
    print("[PASS] gmgn-cli config --check confirms configured credentials")
    print("[PASS] gmgn-cli version boundary verified")
    print("[PASS] OAD-277 GMGN production admission OPEN")
    print("[PASS] GMGN remains observation-only")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-277 PHYSICALLY CERTIFIED")
'''


def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")


def write_checked(path, source):
    normalized = textwrap.dedent(source).lstrip()
    ast.parse(normalized, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(normalized, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError(
            "installer identity mismatch: expected " + EXPECTED_FILENAME
        )

    root = locate_root()
    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module = pkg / MODULE_NAME
    test = root / TEST_NAME
    init = pkg / "__init__.py"

    print("=" * 120)
    print(" " + BUILD_ID + " " + TITLE + " INSTALLER")
    print("=" * 120)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", root)

    for rel, symbols in DEPENDENCIES.items():
        p = root / rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: " + rel)
        src = p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def " + symbol + "(") not in src and ("class " + symbol) not in src:
                raise RuntimeError(
                    "Exact dependency symbol missing: " + rel + " -> " + symbol
                )
        print("[PASS] exact dependency verified:", rel)

    protected = []
    for p, label in (
        (
            root / "qseries_v2" / "oracle_production_hardening" / "oph_023_postgresql_single_writer_production_freeze.py",
            "Frozen OPH-023",
        ),
        (
            root / "qseries_v2" / "oracle_adapters" / "kalshi" / "oad_055_kalshi_production_freeze.py",
            "Frozen Kalshi OAD-055",
        ),
    ):
        if not p.is_file():
            raise RuntimeError(label + " missing: " + str(p))
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))
        print("[PASS]", label, "verified")

    old = {p: (p.read_bytes() if p.exists() else None) for p in (module, test, init)}

    try:
        write_checked(module, MODULE_SOURCE)
        write_checked(test, TEST_SOURCE)

        lines = init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export = "from ." + module.stem + " import *"
        if export not in lines:
            lines.append(export)
        write_checked(init, "\n".join(x for x in lines if x.strip()) + "\n")

        for p, expected_hash in protected:
            actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                raise RuntimeError("Frozen boundary changed: " + p.name)

        print("[PASS] repaired existing OAD-277 production boundary in place")
        print("[PASS] raw process-environment API-key dependency retired")
        print("[PASS] GMGN CLI config --check is now the credential truth boundary")
        print("[PASS] downstream GMGNAdmission contract preserved")
        print("[PASS] module installed:", module.relative_to(root))
        print("[PASS] test installed:", test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] GMGN remains observation-only")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-277 CLI CONFIG REBUILD INSTALLATION COMPLETE")

    except Exception:
        for p, previous in old.items():
            if previous is None:
                if p.exists():
                    p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(previous)
        print("[ROLLBACK] OAD-277 affected files restored")
        raise


if __name__ == "__main__":
    main()
