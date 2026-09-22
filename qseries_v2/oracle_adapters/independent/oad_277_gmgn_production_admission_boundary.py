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
