from __future__ import annotations

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
