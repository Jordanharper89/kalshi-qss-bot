"""OLA-065 Oracle Live Shadow Operator Runtime Integration Gate."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "OLA-065"
ENGINE_ID = "OLA-065"


class OracleLiveShadowOperatorRuntimeIntegrationBlocked(RuntimeError):
    """Raised when the operator runtime boundary is incomplete or unsafe."""


@dataclass(frozen=True, slots=True)
class OracleLiveShadowOperatorRuntimeIntegrationRecord:
    schema_version: str
    engine_id: str
    operator_module_present: bool
    operator_schema_verified: bool
    launcher_present: bool
    start_command_present: bool
    status_command_present: bool
    tail_command_present: bool
    stop_command_present: bool
    pid_control_present: bool
    runtime_freshness_check_present: bool
    detached_process_boundary_present: bool
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    order_placement_allowed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False


class OracleLiveShadowOperatorRuntimeIntegrationGate:
    """Certifies the read-only OLA-064 operator runtime boundary."""

    read_only = True
    execution_allowed = False

    _REQUIRED_SOURCE_MARKERS = (
        'SCHEMA_VERSION = "OLA-064"',
        'ENGINE_ID = "OLA-064"',
        'LAUNCHER = ROOT / "run_oracle_live_shadow_FINAL_FIXED.py"',
        'PID_FILE = OPERATOR_ROOT / "oracle_live_shadow.pid.json"',
        'def _start() -> int:',
        'def _print_status(',
        'def _tail(lines: int) -> int:',
        'def _stop() -> int:',
        'subparsers.add_parser("start")',
        'subparsers.add_parser("stop")',
        'subparsers.add_parser("status")',
        'subparsers.add_parser("tail")',
        'runtime_fresh',
        'execution_allowed',
        'subprocess.Popen(',
    )

    def certify(
        self,
        *,
        repository_root: str | Path,
    ) -> OracleLiveShadowOperatorRuntimeIntegrationRecord:
        root = Path(repository_root).resolve()
        operator_path = root / "oracle_live_shadow_operator.py"
        launcher_path = root / "run_oracle_live_shadow_FINAL_FIXED.py"

        if not operator_path.exists():
            raise OracleLiveShadowOperatorRuntimeIntegrationBlocked(
                f"Missing OLA-064 operator module: {operator_path}"
            )

        if not launcher_path.exists():
            raise OracleLiveShadowOperatorRuntimeIntegrationBlocked(
                f"Missing canonical live-shadow launcher: {launcher_path}"
            )

        source = operator_path.read_text(encoding="utf-8")

        missing = [
            marker
            for marker in self._REQUIRED_SOURCE_MARKERS
            if marker not in source
        ]

        if missing:
            raise OracleLiveShadowOperatorRuntimeIntegrationBlocked(
                "OLA-064 operator runtime contract is incomplete. "
                f"Missing markers: {missing}"
            )

        forbidden_markers = (
            "order_placement_allowed = True",
            "execution_allowed = True",
            "funds_moved = True",
            "portfolio_mutated = True",
        )

        unsafe = [
            marker
            for marker in forbidden_markers
            if marker in source
        ]

        if unsafe:
            raise OracleLiveShadowOperatorRuntimeIntegrationBlocked(
                "Unsafe operator permissions detected: "
                f"{unsafe}"
            )

        compile(source, str(operator_path), "exec")

        return OracleLiveShadowOperatorRuntimeIntegrationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            operator_module_present=True,
            operator_schema_verified=True,
            launcher_present=True,
            start_command_present=True,
            status_command_present=True,
            tail_command_present=True,
            stop_command_present=True,
            pid_control_present=True,
            runtime_freshness_check_present=True,
            detached_process_boundary_present=True,
        )


def certify_oracle_live_shadow_operator_runtime(
    *,
    repository_root: str | Path,
) -> OracleLiveShadowOperatorRuntimeIntegrationRecord:
    return OracleLiveShadowOperatorRuntimeIntegrationGate().certify(
        repository_root=repository_root,
    )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OracleLiveShadowOperatorRuntimeIntegrationBlocked",
    "OracleLiveShadowOperatorRuntimeIntegrationRecord",
    "OracleLiveShadowOperatorRuntimeIntegrationGate",
    "certify_oracle_live_shadow_operator_runtime",
]
