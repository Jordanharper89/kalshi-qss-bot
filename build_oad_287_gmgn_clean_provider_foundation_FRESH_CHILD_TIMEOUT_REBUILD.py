from __future__ import annotations

import ast
import os
import textwrap
from pathlib import Path

EXPECTED_INSTALLER = 'build_oad_287_gmgn_clean_provider_foundation_FRESH_CHILD_TIMEOUT_REBUILD.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport os\nimport shutil\nimport subprocess\nimport time\n\nREAD_ONLY = True\nPROBABILITY_ENABLED = False\nDIRECTION_ENABLED = False\nPUBLICATION_ALLOWED = False\nEXECUTION_AUTHORITY = False\n\nDEFAULT_COMMAND_TIMEOUT_SECONDS = 30.0\n\n\n@dataclass(frozen=True, slots=True)\nclass GMGNCommandResult:\n    command: tuple[str, ...]\n    returncode: int | None\n    stdout: str\n    stderr: str\n    elapsed_seconds: float\n    exception_type: str | None\n    exception_detail: str | None\n\n\n@dataclass(frozen=True, slots=True)\nclass GMGNProviderAdmission:\n    cli_path: str | None\n    config_ok: bool\n    version_ok: bool\n    admitted: bool\n    version_text: str | None = None\n    version_result: GMGNCommandResult | None = None\n    config_result: GMGNCommandResult | None = None\n    execution_authority: bool = False\n\n\nclass GMGNProviderError(RuntimeError):\n    pass\n\n\nclass GMGNRateLimitError(GMGNProviderError):\n    def __init__(self, message: str, retry_after_seconds: float = 300.0):\n        super().__init__(str(message))\n        self.retry_after_seconds = float(retry_after_seconds)\n\n\ndef _candidate_paths():\n    candidates: list[Path] = []\n\n    for name in ("gmgn-cli", "gmgn-cli.cmd"):\n        resolved = shutil.which(name)\n        if resolved:\n            candidates.append(Path(resolved))\n\n    for base in (\n        os.environ.get("APPDATA"),\n        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming"),\n    ):\n        if base:\n            candidates.extend(\n                (\n                    Path(base) / "npm" / "gmgn-cli.cmd",\n                    Path(base) / "npm" / "gmgn-cli",\n                )\n            )\n\n    seen: set[str] = set()\n    for candidate in candidates:\n        normalized = os.path.normcase(\n            os.path.normpath(str(candidate.expanduser().resolve()))\n        )\n        if normalized not in seen:\n            seen.add(normalized)\n            yield Path(normalized)\n\n\ndef locate_gmgn_cli() -> str | None:\n    for candidate in _candidate_paths():\n        if candidate.is_file():\n            return str(candidate)\n    return None\n\n\ndef _command(cli_path: str, args) -> list[str]:\n    cli_path = str(cli_path)\n    argv = [cli_path, *[str(x) for x in args]]\n\n    if os.name == "nt" and Path(cli_path).suffix.lower() in (".cmd", ".bat"):\n        comspec = (\n            os.environ.get("COMSPEC")\n            or os.path.join(\n                os.environ.get("SystemRoot", r"C:\\Windows"),\n                "System32",\n                "cmd.exe",\n            )\n        )\n        return [\n            comspec,\n            "/d",\n            "/s",\n            "/c",\n            subprocess.list2cmdline(argv),\n        ]\n\n    return argv\n\n\ndef run_gmgn_cli(\n    cli_path: str,\n    args,\n    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,\n    text: bool = True,\n):\n    return subprocess.run(\n        _command(cli_path, args),\n        capture_output=True,\n        text=text,\n        timeout=float(timeout_seconds),\n        check=False,\n    )\n\n\ndef _diagnostic_run(\n    cli_path: str,\n    args,\n    timeout_seconds: float,\n) -> GMGNCommandResult:\n    command = tuple(_command(cli_path, args))\n    started = time.monotonic()\n\n    try:\n        completed = subprocess.run(\n            list(command),\n            capture_output=True,\n            text=True,\n            timeout=float(timeout_seconds),\n            check=False,\n        )\n        elapsed = time.monotonic() - started\n        return GMGNCommandResult(\n            command=command,\n            returncode=int(completed.returncode),\n            stdout=(completed.stdout or ""),\n            stderr=(completed.stderr or ""),\n            elapsed_seconds=elapsed,\n            exception_type=None,\n            exception_detail=None,\n        )\n    except Exception as exc:\n        elapsed = time.monotonic() - started\n        return GMGNCommandResult(\n            command=command,\n            returncode=None,\n            stdout="",\n            stderr="",\n            elapsed_seconds=elapsed,\n            exception_type=type(exc).__name__,\n            exception_detail=str(exc),\n        )\n\n\ndef evaluate_gmgn_provider(\n    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,\n) -> GMGNProviderAdmission:\n    cli_path = locate_gmgn_cli()\n\n    if not cli_path:\n        return GMGNProviderAdmission(\n            cli_path=None,\n            config_ok=False,\n            version_ok=False,\n            admitted=False,\n            execution_authority=False,\n        )\n\n    version_result = _diagnostic_run(\n        cli_path,\n        ["--version"],\n        timeout_seconds,\n    )\n    version_text = (version_result.stdout or version_result.stderr or "").strip()\n    version_ok = (\n        version_result.exception_type is None\n        and version_result.returncode == 0\n        and bool(version_text)\n    )\n\n    config_result = _diagnostic_run(\n        cli_path,\n        ["config", "--check"],\n        timeout_seconds,\n    )\n    config_ok = (\n        config_result.exception_type is None\n        and config_result.returncode == 0\n    )\n\n    return GMGNProviderAdmission(\n        cli_path=cli_path,\n        config_ok=config_ok,\n        version_ok=version_ok,\n        admitted=bool(version_ok and config_ok),\n        version_text=version_text or None,\n        version_result=version_result,\n        config_result=config_result,\n        execution_authority=False,\n    )\n\n\ndef _failure_detail(label: str, result: GMGNCommandResult | None) -> str:\n    if result is None:\n        return f"{label}=NO_RESULT"\n\n    stdout = (result.stdout or "").strip()\n    stderr = (result.stderr or "").strip()\n    return (\n        f"{label}: command={list(result.command)!r} "\n        f"returncode={result.returncode!r} "\n        f"elapsed_seconds={result.elapsed_seconds:.3f} "\n        f"exception_type={result.exception_type!r} "\n        f"exception_detail={result.exception_detail!r} "\n        f"stdout={stdout[:500]!r} "\n        f"stderr={stderr[:500]!r}"\n    )\n\n\ndef require_gmgn_provider(\n    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,\n) -> GMGNProviderAdmission:\n    admission = evaluate_gmgn_provider(timeout_seconds)\n\n    if not admission.cli_path:\n        raise GMGNProviderError("GMGN_NOT_ADMITTED: cli not found")\n\n    if not admission.version_ok:\n        raise GMGNProviderError(\n            "GMGN_NOT_ADMITTED: version check failed | "\n            + _failure_detail("version", admission.version_result)\n        )\n\n    if not admission.config_ok:\n        raise GMGNProviderError(\n            "GMGN_NOT_ADMITTED: config check failed | "\n            + _failure_detail("config", admission.config_result)\n        )\n\n    return admission\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport subprocess\nimport sys\nimport unittest\nfrom pathlib import Path\n\nimport qseries_v2.oracle_adapters.independent.oad_287_gmgn_clean_provider_foundation as M\n\n\nclass T(unittest.TestCase):\n    def test_01_direct_physical_admission(self):\n        a = M.require_gmgn_provider()\n        print("[GMGN] cli_path=", a.cli_path)\n        print("[GMGN] version=", a.version_text)\n        print(\n            "[GMGN] version_elapsed_seconds=",\n            round(a.version_result.elapsed_seconds, 3)\n            if a.version_result\n            else None,\n        )\n        print(\n            "[GMGN] config_elapsed_seconds=",\n            round(a.config_result.elapsed_seconds, 3)\n            if a.config_result\n            else None,\n        )\n        print("[GMGN] admitted=", a.admitted)\n        self.assertTrue(a.admitted)\n        self.assertFalse(a.execution_authority)\n\n    def test_02_fresh_python_child_physical_admission(self):\n        code = r"""\nfrom qseries_v2.oracle_adapters.independent.oad_287_gmgn_clean_provider_foundation import require_gmgn_provider\na = require_gmgn_provider()\nprint("[CHILD] cli_path=", a.cli_path)\nprint("[CHILD] version=", a.version_text)\nprint("[CHILD] version_elapsed_seconds=", round(a.version_result.elapsed_seconds, 3) if a.version_result else None)\nprint("[CHILD] config_elapsed_seconds=", round(a.config_result.elapsed_seconds, 3) if a.config_result else None)\nprint("[CHILD] admitted=", a.admitted)\n"""\n        p = subprocess.run(\n            [sys.executable, "-c", code],\n            cwd=Path.cwd(),\n            text=True,\n            capture_output=True,\n            timeout=120,\n            check=False,\n        )\n        print(p.stdout, end="")\n        print(p.stderr, end="")\n        self.assertEqual(p.returncode, 0)\n        self.assertIn("[CHILD] admitted= True", p.stdout)\n\n    def test_03_safety_boundary(self):\n        self.assertTrue(M.READ_ONLY)\n        self.assertFalse(M.PROBABILITY_ENABLED)\n        self.assertFalse(M.DIRECTION_ENABLED)\n        self.assertFalse(M.PUBLICATION_ALLOWED)\n        self.assertFalse(M.EXECUTION_AUTHORITY)\n\n\nif __name__ == "__main__":\n    result = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] direct GMGN admission physically verified")\n    print("[PASS] fresh Python child GMGN admission physically verified")\n    print("[PASS] command timeout raised to 30 seconds")\n    print("[PASS] exact failure diagnostics preserved")\n    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")\n    print("[DONE] OAD-287 CLEAN PROVIDER FOUNDATION REBUILD CERTIFIED")\n'


def repository_root() -> Path:
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for candidate in (base, *base.parents):
            if (candidate / "qseries_v2").is_dir():
                return candidate
    raise RuntimeError("Q Series repository root not found")


def write_checked(path: Path, source: str) -> None:
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(temp, path)


def main() -> None:
    if Path(__file__).name != EXPECTED_INSTALLER:
        raise RuntimeError("installer filename identity mismatch")

    root = repository_root()

    for relative in (
        "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
        "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    ):
        if not (root / relative).is_file():
            raise RuntimeError("frozen boundary missing: " + relative)

    package = root / "qseries_v2" / "oracle_adapters" / "independent"
    module_path = package / "oad_287_gmgn_clean_provider_foundation.py"
    test_path = root / "test_oad_287_gmgn_clean_provider_foundation.py"

    if not module_path.is_file():
        raise RuntimeError("existing OAD-287 replacement foundation missing")

    backup = module_path.with_suffix(".py.pre_fresh_child_timeout_rebuild")
    backup.write_bytes(module_path.read_bytes())

    try:
        write_checked(module_path, MODULE_SOURCE)
        write_checked(test_path, TEST_SOURCE)
    except Exception:
        module_path.write_bytes(backup.read_bytes())
        raise

    print("[PASS] OAD-287 clean provider foundation rebuilt in place")
    print("[PASS] fresh-child command timeout increased from 10s to 30s")
    print("[PASS] version/config execution now preserves exact physical failure details")
    print("[PASS] Windows npm .cmd execution remains centralized through COMSPEC")
    print("[PASS] frozen OPH-023/Kalshi OAD-055 preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-287 FRESH-CHILD TIMEOUT REBUILD INSTALLED")


if __name__ == "__main__":
    main()
