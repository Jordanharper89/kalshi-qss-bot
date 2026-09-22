from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess
import time

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False

DEFAULT_COMMAND_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class GMGNCommandResult:
    command: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float
    exception_type: str | None
    exception_detail: str | None


@dataclass(frozen=True, slots=True)
class GMGNProviderAdmission:
    cli_path: str | None
    config_ok: bool
    version_ok: bool
    admitted: bool
    version_text: str | None = None
    version_result: GMGNCommandResult | None = None
    config_result: GMGNCommandResult | None = None
    execution_authority: bool = False


class GMGNProviderError(RuntimeError):
    pass


class GMGNRateLimitError(GMGNProviderError):
    def __init__(self, message: str, retry_after_seconds: float = 300.0):
        super().__init__(str(message))
        self.retry_after_seconds = float(retry_after_seconds)


def _candidate_paths():
    candidates: list[Path] = []

    for name in ("gmgn-cli", "gmgn-cli.cmd"):
        resolved = shutil.which(name)
        if resolved:
            candidates.append(Path(resolved))

    for base in (
        os.environ.get("APPDATA"),
        os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming"),
    ):
        if base:
            candidates.extend(
                (
                    Path(base) / "npm" / "gmgn-cli.cmd",
                    Path(base) / "npm" / "gmgn-cli",
                )
            )

    seen: set[str] = set()
    for candidate in candidates:
        normalized = os.path.normcase(
            os.path.normpath(str(candidate.expanduser().resolve()))
        )
        if normalized not in seen:
            seen.add(normalized)
            yield Path(normalized)


def locate_gmgn_cli() -> str | None:
    for candidate in _candidate_paths():
        if candidate.is_file():
            return str(candidate)
    return None


def _command(cli_path: str, args) -> list[str]:
    cli_path = str(cli_path)
    argv = [cli_path, *[str(x) for x in args]]

    if os.name == "nt" and Path(cli_path).suffix.lower() in (".cmd", ".bat"):
        comspec = (
            os.environ.get("COMSPEC")
            or os.path.join(
                os.environ.get("SystemRoot", r"C:\Windows"),
                "System32",
                "cmd.exe",
            )
        )
        return [
            comspec,
            "/d",
            "/s",
            "/c",
            subprocess.list2cmdline(argv),
        ]

    return argv


def run_gmgn_cli(
    cli_path: str,
    args,
    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
    text: bool = True,
):
    return subprocess.run(
        _command(cli_path, args),
        capture_output=True,
        text=text,
        timeout=float(timeout_seconds),
        check=False,
    )


def _diagnostic_run(
    cli_path: str,
    args,
    timeout_seconds: float,
) -> GMGNCommandResult:
    command = tuple(_command(cli_path, args))
    started = time.monotonic()

    try:
        completed = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=float(timeout_seconds),
            check=False,
        )
        elapsed = time.monotonic() - started
        return GMGNCommandResult(
            command=command,
            returncode=int(completed.returncode),
            stdout=(completed.stdout or ""),
            stderr=(completed.stderr or ""),
            elapsed_seconds=elapsed,
            exception_type=None,
            exception_detail=None,
        )
    except Exception as exc:
        elapsed = time.monotonic() - started
        return GMGNCommandResult(
            command=command,
            returncode=None,
            stdout="",
            stderr="",
            elapsed_seconds=elapsed,
            exception_type=type(exc).__name__,
            exception_detail=str(exc),
        )


def evaluate_gmgn_provider(
    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
) -> GMGNProviderAdmission:
    cli_path = locate_gmgn_cli()

    if not cli_path:
        return GMGNProviderAdmission(
            cli_path=None,
            config_ok=False,
            version_ok=False,
            admitted=False,
            execution_authority=False,
        )

    version_result = _diagnostic_run(
        cli_path,
        ["--version"],
        timeout_seconds,
    )
    version_text = (version_result.stdout or version_result.stderr or "").strip()
    version_ok = (
        version_result.exception_type is None
        and version_result.returncode == 0
        and bool(version_text)
    )

    config_result = _diagnostic_run(
        cli_path,
        ["config", "--check"],
        timeout_seconds,
    )
    config_ok = (
        config_result.exception_type is None
        and config_result.returncode == 0
    )

    return GMGNProviderAdmission(
        cli_path=cli_path,
        config_ok=config_ok,
        version_ok=version_ok,
        admitted=bool(version_ok and config_ok),
        version_text=version_text or None,
        version_result=version_result,
        config_result=config_result,
        execution_authority=False,
    )


def _failure_detail(label: str, result: GMGNCommandResult | None) -> str:
    if result is None:
        return f"{label}=NO_RESULT"

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    return (
        f"{label}: command={list(result.command)!r} "
        f"returncode={result.returncode!r} "
        f"elapsed_seconds={result.elapsed_seconds:.3f} "
        f"exception_type={result.exception_type!r} "
        f"exception_detail={result.exception_detail!r} "
        f"stdout={stdout[:500]!r} "
        f"stderr={stderr[:500]!r}"
    )


def require_gmgn_provider(
    timeout_seconds: float = DEFAULT_COMMAND_TIMEOUT_SECONDS,
) -> GMGNProviderAdmission:
    admission = evaluate_gmgn_provider(timeout_seconds)

    if not admission.cli_path:
        raise GMGNProviderError("GMGN_NOT_ADMITTED: cli not found")

    if not admission.version_ok:
        raise GMGNProviderError(
            "GMGN_NOT_ADMITTED: version check failed | "
            + _failure_detail("version", admission.version_result)
        )

    if not admission.config_ok:
        raise GMGNProviderError(
            "GMGN_NOT_ADMITTED: config check failed | "
            + _failure_detail("config", admission.config_result)
        )

    return admission
