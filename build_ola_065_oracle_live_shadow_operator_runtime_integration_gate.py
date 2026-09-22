from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_live_shadow_operator_runtime_integration_gate.py"
)

TEST = (
    ROOT
    / "test_ola_065_oracle_live_shadow_operator_runtime_integration_gate.py"
)

OPERATOR = ROOT / "oracle_live_shadow_operator.py"

MODULE_SOURCE = r'''"""OLA-065 Oracle Live Shadow Operator Runtime Integration Gate."""

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
'''

TEST_SOURCE = r'''from __future__ import annotations

import tempfile
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_runtime_integration_gate import (
    OracleLiveShadowOperatorRuntimeIntegrationBlocked,
    OracleLiveShadowOperatorRuntimeIntegrationGate,
    certify_oracle_live_shadow_operator_runtime,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    record = certify_oracle_live_shadow_operator_runtime(
        repository_root=ROOT,
    )

    assert record.schema_version == "OLA-065"
    assert record.engine_id == "OLA-065"
    assert record.operator_module_present is True
    assert record.operator_schema_verified is True
    assert record.launcher_present is True
    assert record.start_command_present is True
    assert record.status_command_present is True
    assert record.tail_command_present is True
    assert record.stop_command_present is True
    assert record.pid_control_present is True
    assert record.runtime_freshness_check_present is True
    assert record.detached_process_boundary_present is True
    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.alerts_allowed is False
    assert record.qseries_handoff_allowed is False
    assert record.order_placement_allowed is False
    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    gate = OracleLiveShadowOperatorRuntimeIntegrationGate()

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)

        try:
            gate.certify(repository_root=temporary_root)
        except OracleLiveShadowOperatorRuntimeIntegrationBlocked:
            pass
        else:
            raise AssertionError(
                "OLA-065 must reject a missing operator module"
            )

        fake_operator = temporary_root / "oracle_live_shadow_operator.py"
        fake_launcher = (
            temporary_root / "run_oracle_live_shadow_FINAL_FIXED.py"
        )

        fake_operator.write_text(
            'SCHEMA_VERSION = "OLA-064"\n',
            encoding="utf-8",
        )
        fake_launcher.write_text(
            'raise SystemExit(0)\n',
            encoding="utf-8",
        )

        try:
            gate.certify(repository_root=temporary_root)
        except OracleLiveShadowOperatorRuntimeIntegrationBlocked:
            pass
        else:
            raise AssertionError(
                "OLA-065 must reject an incomplete operator contract"
            )

    print(
        "[PASS] OLA-065 Oracle Live Shadow "
        "Operator Runtime Integration Gate"
    )
    print(
        {
            "schema_version": "OLA-065",
            "engine_id": "OLA-065",
            "status": "passed",
            "ola064_operator_verified": True,
            "canonical_launcher_verified": True,
            "operator_commands_verified": (
                "start",
                "status",
                "tail",
                "stop",
            ),
            "pid_control_verified": True,
            "runtime_freshness_verified": True,
            "detached_process_boundary_verified": True,
            "missing_operator_rejected": True,
            "incomplete_operator_rejected": True,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_full_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path}")


def main() -> int:
    print("========================================")
    print(" OLA-065 INSTALLER")
    print(" ORACLE LIVE SHADOW OPERATOR")
    print(" RUNTIME INTEGRATION GATE")
    print("========================================")

    if not OPERATOR.exists():
        raise SystemExit(
            f"[ERROR] Missing OLA-064 operator module: {OPERATOR}"
        )

    launcher = ROOT / "run_oracle_live_shadow_FINAL_FIXED.py"
    if not launcher.exists():
        raise SystemExit(
            f"[ERROR] Missing canonical launcher: {launcher}"
        )

    operator_source = OPERATOR.read_text(encoding="utf-8")

    required_ola064_markers = (
        'SCHEMA_VERSION = "OLA-064"',
        'ENGINE_ID = "OLA-064"',
        'def _start() -> int:',
        'def _stop() -> int:',
        'def _tail(lines: int) -> int:',
        'def _print_status(',
    )

    missing = [
        marker
        for marker in required_ola064_markers
        if marker not in operator_source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-064 operator installation is incomplete. "
            f"Missing markers: {missing}"
        )

    write_full_replacement(MODULE, MODULE_SOURCE)
    write_full_replacement(TEST, TEST_SOURCE)

    compile(
        MODULE.read_text(encoding="utf-8"),
        str(MODULE),
        "exec",
    )
    compile(
        TEST.read_text(encoding="utf-8"),
        str(TEST),
        "exec",
    )

    print("")
    print(
        "[DONE] OLA-065 Oracle live-shadow operator "
        "runtime integration gate installed"
    )
    print("")
    print("Run:")
    print(
        "py test_ola_065_oracle_live_shadow_"
        "operator_runtime_integration_gate.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())