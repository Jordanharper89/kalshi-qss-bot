from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

from qseries_v2.oracle_intelligence.live_acquisition import (
    oracle_continuous_operator_launch_readiness_gate as ola076,
)


VALID_OLA075 = '''from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = "OLA-075"
ENGINE_ID = "OLA-075"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


@dataclass(frozen=True, slots=True)
class OLA075Record:
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False


def main() -> int:
    raise AssertionError(
        "OLA-075 main() must never be invoked by OLA-076"
    )
'''


VALID_OLA074 = '''from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = "OLA-074"
ENGINE_ID = "OLA-074"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


@dataclass(frozen=True, slots=True)
class OLA074Record:
    schema_version: str = SCHEMA_VERSION
    engine_id: str = ENGINE_ID
    read_only: bool = True
    execution_allowed: bool = False


def main() -> int:
    raise AssertionError(
        "OLA-074 main() must never be invoked by OLA-076"
    )
'''


def write_source(
    path: Path,
    source: str,
) -> None:
    path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    os.utime(
        path,
        None,
    )


def expect_dependency_error(
    label: str,
    callable_under_test,
) -> None:
    try:
        callable_under_test()
    except ola076.OracleContinuousDependencyError:
        return

    raise AssertionError(
        f"{label} expected OracleContinuousDependencyError"
    )


def temporary_ola076_modules() -> set[str]:
    return {
        name
        for name in sys.modules
        if name.startswith("_ola076_dependency_")
    }


def main() -> int:
    print("========================================")
    print(" OLA-076 LAUNCH READINESS GATE TEST")
    print(" FRESH-SOURCE IMPORT CORRECTION V3")
    print(" NO REAL CONTINUOUS SERVICE START")
    print("========================================")

    assert ola076.SCHEMA_VERSION == "OLA-076"
    assert ola076.ENGINE_ID == "OLA-076"

    assert ola076.READ_ONLY is True
    assert ola076.EXECUTION_ALLOWED is False
    assert ola076.ALERTS_ALLOWED is False
    assert ola076.QSERIES_HANDOFF_ALLOWED is False
    assert ola076.EXECUTION_ADAPTER_RESOLVED is False
    assert ola076.EXECUTION_ADAPTER_INVOKED is False
    assert ola076.TRADE_AUTHORIZATION_ALLOWED is False
    assert ola076.ORDER_PLACEMENT_ALLOWED is False
    assert ola076.FUNDS_MOVED is False
    assert ola076.PORTFOLIO_MUTATED is False

    gate = ola076.OracleContinuousOperatorLaunchReadinessGate()

    assert gate.read_only is True
    assert gate.execution_allowed is False

    baseline_temporary_modules = temporary_ola076_modules()

    service_start_calls: list[str] = []

    def forbidden_process_start(*args, **kwargs):
        service_start_calls.append("process")
        raise AssertionError(
            "OLA-076 must not create a process"
        )

    def forbidden_thread_start(*args, **kwargs):
        service_start_calls.append("thread")
        raise AssertionError(
            "OLA-076 must not start a thread"
        )

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)

        ola075_path = root / "ola075_dependency.py"
        ola074_path = root / "ola074_dependency.py"

        write_source(
            ola075_path,
            VALID_OLA075,
        )

        write_source(
            ola074_path,
            VALID_OLA074,
        )

        print("[TEST] Valid OLA-075 and OLA-074 dependencies")

        with (
            patch(
                "subprocess.Popen",
                side_effect=forbidden_process_start,
            ),
            patch(
                "threading.Thread.start",
                side_effect=forbidden_thread_start,
            ),
        ):
            first_record = gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            )

        first_record.assert_invariants()

        assert first_record.schema_version == "OLA-076"
        assert first_record.engine_id == "OLA-076"
        assert first_record.readiness_status == "ready"
        assert first_record.launch_ready is True
        assert first_record.dependency_count == 2

        assert first_record.ola075_dependency.dependency_label == "OLA-075"
        assert first_record.ola074_dependency.dependency_label == "OLA-074"

        assert first_record.unique_module_names_used is True
        assert first_record.current_disk_sources_executed is True
        assert first_record.bytecode_cache_bypassed is True
        assert first_record.temporary_modules_cleaned is True

        assert first_record.dependency_main_callables_verified is True
        assert first_record.dependency_main_callables_invoked is False
        assert first_record.real_continuous_service_started is False
        assert first_record.process_created is False
        assert first_record.thread_created is False
        assert first_record.background_loop_started is False

        assert first_record.read_only is True
        assert first_record.execution_allowed is False
        assert first_record.alerts_allowed is False
        assert first_record.qseries_handoff_allowed is False
        assert first_record.execution_adapter_resolved is False
        assert first_record.execution_adapter_invoked is False
        assert first_record.trade_authorization_allowed is False
        assert first_record.order_placement_allowed is False
        assert first_record.funds_moved is False
        assert first_record.portfolio_mutated is False

        assert service_start_calls == []

        assert (
            first_record.ola075_dependency.temporary_module_name
            not in sys.modules
        )

        assert (
            first_record.ola074_dependency.temporary_module_name
            not in sys.modules
        )

        first_ola075_module_name = (
            first_record.ola075_dependency.temporary_module_name
        )

        first_ola074_module_name = (
            first_record.ola074_dependency.temporary_module_name
        )

        first_ola075_hash = (
            first_record.ola075_dependency.dependency_source_hash
        )

        first_ola074_hash = (
            first_record.ola074_dependency.dependency_source_hash
        )

        print("[OK] Valid dependencies passed")

        print("[TEST] Immediate rewritten OLA-075 schema detection")

        invalid_ola075_schema = VALID_OLA075.replace(
            'SCHEMA_VERSION = "OLA-075"',
            'SCHEMA_VERSION = "OLA-999"',
            1,
        )

        write_source(
            ola075_path,
            invalid_ola075_schema,
        )

        expect_dependency_error(
            "Incorrect OLA-075 dependency schema",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        print("[OK] Rewritten OLA-075 schema rejected immediately")

        write_source(
            ola075_path,
            VALID_OLA075,
        )

        second_record = gate.evaluate(
            ola075_path=ola075_path,
            ola074_path=ola074_path,
        )

        second_record.assert_invariants()

        assert (
            second_record.ola075_dependency.temporary_module_name
            != first_ola075_module_name
        )

        assert (
            second_record.ola074_dependency.temporary_module_name
            != first_ola074_module_name
        )

        assert (
            second_record.ola075_dependency.dependency_source_hash
            == first_ola075_hash
        )

        assert (
            second_record.ola074_dependency.dependency_source_hash
            == first_ola074_hash
        )

        assert temporary_ola076_modules() == baseline_temporary_modules

        print("[TEST] Immediate rewritten OLA-074 engine detection")

        invalid_ola074_engine = VALID_OLA074.replace(
            'ENGINE_ID = "OLA-074"',
            'ENGINE_ID = "OLA-999"',
            1,
        )

        write_source(
            ola074_path,
            invalid_ola074_engine,
        )

        expect_dependency_error(
            "Incorrect OLA-074 dependency engine",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        print("[OK] Rewritten OLA-074 engine rejected immediately")

        write_source(
            ola074_path,
            VALID_OLA074,
        )

        third_record = (
            ola076.evaluate_continuous_operator_launch_readiness(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            )
        )

        third_record.assert_invariants()

        assert (
            third_record.ola075_dependency.temporary_module_name
            != second_record.ola075_dependency.temporary_module_name
        )

        assert (
            third_record.ola074_dependency.temporary_module_name
            != second_record.ola074_dependency.temporary_module_name
        )

        print("[TEST] Missing dependency callable main()")

        missing_main_ola075 = VALID_OLA075.replace(
            '''def main() -> int:
    raise AssertionError(
        "OLA-075 main() must never be invoked by OLA-076"
    )
''',
            '''main = None
''',
            1,
        )

        write_source(
            ola075_path,
            missing_main_ola075,
        )

        expect_dependency_error(
            "Missing OLA-075 callable main()",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        print("[OK] Missing callable main() rejected")

        print("[TEST] Execution-enabled dependency")

        execution_enabled_ola075 = VALID_OLA075.replace(
            "EXECUTION_ALLOWED = False",
            "EXECUTION_ALLOWED = True",
            1,
        )

        write_source(
            ola075_path,
            execution_enabled_ola075,
        )

        expect_dependency_error(
            "Execution-enabled OLA-075 dependency",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        print("[OK] Execution-enabled OLA-075 rejected")

        write_source(
            ola075_path,
            VALID_OLA075,
        )

        execution_enabled_ola074 = VALID_OLA074.replace(
            "EXECUTION_ALLOWED = False",
            "EXECUTION_ALLOWED = True",
            1,
        )

        write_source(
            ola074_path,
            execution_enabled_ola074,
        )

        expect_dependency_error(
            "Execution-enabled OLA-074 dependency",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        print("[OK] Execution-enabled OLA-074 rejected")

        print("[TEST] Prohibited order authority")

        write_source(
            ola074_path,
            VALID_OLA074.replace(
                "ORDER_PLACEMENT_ALLOWED = False",
                "ORDER_PLACEMENT_ALLOWED = True",
                1,
            ),
        )

        expect_dependency_error(
            "Order-enabled OLA-074 dependency",
            lambda: gate.evaluate(
                ola075_path=ola075_path,
                ola074_path=ola074_path,
            ),
        )

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

        print("[OK] Prohibited order authority rejected")

        write_source(
            ola074_path,
            VALID_OLA074,
        )

        final_record = gate.attest(
            ola075_path=ola075_path,
            ola074_path=ola074_path,
        )

        final_payload = final_record.to_dict()

        assert final_payload["launch_ready"] is True
        assert final_payload["read_only"] is True
        assert final_payload["execution_allowed"] is False
        assert final_payload["real_continuous_service_started"] is False

        assert temporary_ola076_modules() == baseline_temporary_modules
        assert service_start_calls == []

    print(
        "[PASS] OLA-076 Oracle Continuous Operator "
        "Launch Readiness Gate Correction V3"
    )

    print({
        "schema_version": "OLA-076",
        "engine_id": "OLA-076",
        "status": "passed",
        "python_314_dataclass_module_registration_preserved": True,
        "unique_module_name_per_dynamic_load": True,
        "unique_name_uses_path_hash_source_hash_and_uuid": True,
        "current_disk_source_executed_every_time": True,
        "standard_bytecode_cache_bypassed": True,
        "import_caches_invalidated": True,
        "temporary_module_registration_cleaned": True,
        "valid_ola075_dependency_passed": True,
        "valid_ola074_dependency_passed": True,
        "rewritten_ola075_invalid_schema_detected_immediately": True,
        "rewritten_ola074_invalid_engine_detected_immediately": True,
        "missing_callable_main_rejected": True,
        "execution_enabled_dependency_rejected": True,
        "prohibited_authority_flag_rejected": True,
        "stale_module_reuse_prevented": True,
        "stale_bytecode_reuse_prevented": True,
        "dependency_main_not_invoked": True,
        "real_continuous_service_started": False,
        "process_created": False,
        "thread_created": False,
        "background_loop_started": False,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    })

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
