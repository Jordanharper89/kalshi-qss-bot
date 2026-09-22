from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parent

ENTRY_POINT_FILE = (
    ROOT
    / "run_oracle_live_shadow_CONTINUOUS.py"
)


def _load_entry_point():
    specification = (
        importlib.util.spec_from_file_location(
            "ola075_entry_point_under_test",
            ENTRY_POINT_FILE,
        )
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise RuntimeError(
            "Could not load OLA-075 operator entry point"
        )

    module = (
        importlib.util.module_from_spec(
            specification
        )
    )

    specification.loader.exec_module(
        module
    )

    return module


class FakeGuardedLauncher:
    SCHEMA_VERSION = "OLA-074"
    ENGINE_ID = "OLA-074"
    READ_ONLY = True
    EXECUTION_ALLOWED = False

    def __init__(
        self,
        return_value: object = 0,
    ) -> None:
        self.return_value = return_value
        self.call_count = 0

    def main(self) -> object:
        self.call_count += 1
        return self.return_value


def _assert_raises(
    expected_exception: type[BaseException],
    callable_object,
) -> BaseException:
    try:
        callable_object()
    except expected_exception as exc:
        return exc

    raise AssertionError(
        "Expected exception was not raised: "
        f"{expected_exception.__name__}"
    )


def main() -> None:
    print("========================================")
    print(" OLA-075 OPERATOR ENTRY POINT TEST")
    print(" DETERMINISTIC DELEGATION VALIDATION")
    print(" NO REAL CONTINUOUS SERVICE START")
    print("========================================")

    module = _load_entry_point()

    assert (
        module.SCHEMA_VERSION
        == "OLA-075"
    )

    assert (
        module.ENGINE_ID
        == "OLA-075"
    )

    assert module.READ_ONLY is True
    assert module.EXECUTION_ALLOWED is False
    assert (
        module.ORDER_PLACEMENT_ALLOWED
        is False
    )
    assert (
        module.FUNDS_MOVEMENT_ALLOWED
        is False
    )
    assert (
        module.PORTFOLIO_MUTATION_ALLOWED
        is False
    )

    print(
        "[OK] OLA-075 static contract verified"
    )

    module._validate_read_only_boundary()

    print(
        "[OK] Read-only boundary validation passed"
    )

    assert (
        module._normalize_exit_code(
            None
        )
        == 0
    )

    assert (
        module._normalize_exit_code(
            True
        )
        == 0
    )

    assert (
        module._normalize_exit_code(
            False
        )
        == 1
    )

    assert (
        module._normalize_exit_code(
            0
        )
        == 0
    )

    assert (
        module._normalize_exit_code(
            7
        )
        == 7
    )

    _assert_raises(
        module.OracleGuardedLauncherContractError,
        lambda: module._normalize_exit_code(
            "invalid"
        ),
    )

    print(
        "[OK] Guarded launcher exit-code "
        "normalization verified"
    )

    original_loader = (
        module._load_guarded_launcher
    )

    try:
        successful_launcher = (
            FakeGuardedLauncher(
                return_value=0
            )
        )

        module._load_guarded_launcher = (
            lambda: successful_launcher
        )

        print(
            "[TEST] Successful guarded delegation"
        )

        successful_exit_code = (
            module.main()
        )

        assert successful_exit_code == 0

        assert (
            successful_launcher.call_count
            == 1
        )

        print(
            "[OK] Guarded launcher called exactly once"
        )

        nonzero_launcher = (
            FakeGuardedLauncher(
                return_value=9
            )
        )

        module._load_guarded_launcher = (
            lambda: nonzero_launcher
        )

        print(
            "[TEST] Nonzero guarded exit propagation"
        )

        nonzero_exit_code = module.main()

        assert nonzero_exit_code == 9

        assert (
            nonzero_launcher.call_count
            == 1
        )

        print(
            "[OK] Guarded exit code propagated"
        )

        none_launcher = (
            FakeGuardedLauncher(
                return_value=None
            )
        )

        module._load_guarded_launcher = (
            lambda: none_launcher
        )

        print(
            "[TEST] None return normalization"
        )

        none_exit_code = module.main()

        assert none_exit_code == 0

        assert (
            none_launcher.call_count
            == 1
        )

        print(
            "[OK] None return normalized to zero"
        )

        invalid_launcher = (
            FakeGuardedLauncher(
                return_value={
                    "unexpected": True,
                }
            )
        )

        module._load_guarded_launcher = (
            lambda: invalid_launcher
        )

        print(
            "[TEST] Invalid guarded result rejection"
        )

        _assert_raises(
            module.OracleGuardedLauncherContractError,
            module.main,
        )

        assert (
            invalid_launcher.call_count
            == 1
        )

        print(
            "[OK] Invalid guarded result rejected"
        )

        class InterruptingLauncher:
            SCHEMA_VERSION = "OLA-074"
            ENGINE_ID = "OLA-074"
            READ_ONLY = True
            EXECUTION_ALLOWED = False

            def __init__(self) -> None:
                self.call_count = 0

            def main(self) -> object:
                self.call_count += 1
                raise KeyboardInterrupt()

        interrupting_launcher = (
            InterruptingLauncher()
        )

        module._load_guarded_launcher = (
            lambda: interrupting_launcher
        )

        print(
            "[TEST] Operator interrupt propagation"
        )

        try:
            module.main()
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError(
                "KeyboardInterrupt was swallowed "
                "inside OLA-075 main()"
            )

        assert (
            interrupting_launcher.call_count
            == 1
        )

        print(
            "[OK] Operator interrupt preserved"
        )

    finally:
        module._load_guarded_launcher = (
            original_loader
        )

    original_read_only = module.READ_ONLY

    try:
        module.READ_ONLY = False

        _assert_raises(
            module.OracleContinuousOperatorEntryPointError,
            module._validate_read_only_boundary,
        )

    finally:
        module.READ_ONLY = original_read_only

    print(
        "[OK] Read-only boundary violation rejected"
    )

    fake_valid_module = SimpleNamespace(
        SCHEMA_VERSION="OLA-074",
        ENGINE_ID="OLA-074",
        READ_ONLY=True,
        EXECUTION_ALLOWED=False,
        main=lambda: 0,
    )

    fake_bad_schema_module = SimpleNamespace(
        SCHEMA_VERSION="OLA-999",
        ENGINE_ID="OLA-074",
        READ_ONLY=True,
        EXECUTION_ALLOWED=False,
        main=lambda: 0,
    )

    fake_bad_engine_module = SimpleNamespace(
        SCHEMA_VERSION="OLA-074",
        ENGINE_ID="OLA-999",
        READ_ONLY=True,
        EXECUTION_ALLOWED=False,
        main=lambda: 0,
    )

    fake_missing_main_module = SimpleNamespace(
        SCHEMA_VERSION="OLA-074",
        ENGINE_ID="OLA-074",
        READ_ONLY=True,
        EXECUTION_ALLOWED=False,
    )

    fake_execution_enabled_module = SimpleNamespace(
        SCHEMA_VERSION="OLA-074",
        ENGINE_ID="OLA-074",
        READ_ONLY=True,
        EXECUTION_ALLOWED=True,
        main=lambda: 0,
    )

    original_module_loader = (
        module._load_module_from_path
    )

    try:
        module._load_module_from_path = (
            lambda path, module_name: fake_valid_module
        )

        resolved_module = (
            module._load_guarded_launcher()
        )

        assert (
            resolved_module
            is fake_valid_module
        )

        module._load_module_from_path = (
            lambda path, module_name: (
                fake_bad_schema_module
            )
        )

        _assert_raises(
            module.OracleGuardedLauncherContractError,
            module._load_guarded_launcher,
        )

        module._load_module_from_path = (
            lambda path, module_name: (
                fake_bad_engine_module
            )
        )

        _assert_raises(
            module.OracleGuardedLauncherContractError,
            module._load_guarded_launcher,
        )

        module._load_module_from_path = (
            lambda path, module_name: (
                fake_missing_main_module
            )
        )

        _assert_raises(
            module.OracleGuardedLauncherContractError,
            module._load_guarded_launcher,
        )

        module._load_module_from_path = (
            lambda path, module_name: (
                fake_execution_enabled_module
            )
        )

        _assert_raises(
            module.OracleGuardedLauncherContractError,
            module._load_guarded_launcher,
        )

    finally:
        module._load_module_from_path = (
            original_module_loader
        )

    print(
        "[OK] Exact OLA-074 dependency "
        "contract enforced"
    )

    source = ENTRY_POINT_FILE.read_text(
        encoding="utf-8"
    )

    required_markers = (
        'SCHEMA_VERSION = "OLA-075"',
        'ENGINE_ID = "OLA-075"',
        'REQUIRED_GUARDED_SCHEMA_VERSION = "OLA-074"',
        "run_oracle_live_shadow_CONTINUOUS_GUARDED.py",
        "_validate_read_only_boundary",
        "_load_guarded_launcher",
        "_normalize_exit_code",
        "guarded_launcher",
        "guarded_main()",
        "except KeyboardInterrupt:",
        "sys.exit(130)",
        "READ_ONLY = True",
        "EXECUTION_ALLOWED = False",
        "ORDER_PLACEMENT_ALLOWED = False",
        "FUNDS_MOVEMENT_ALLOWED = False",
        "PORTFOLIO_MUTATION_ALLOWED = False",
    )

    missing_markers = tuple(
        marker
        for marker in required_markers
        if marker not in source
    )

    if missing_markers:
        raise AssertionError(
            "OLA-075 source is incomplete: "
            f"{missing_markers}"
        )

    forbidden_markers = (
        "requests.post(",
        "place_order(",
        "submit_order(",
        "execute_trade(",
        "execution_allowed = True",
        "ORDER_PLACEMENT_ALLOWED = True",
        "FUNDS_MOVEMENT_ALLOWED = True",
        "PORTFOLIO_MUTATION_ALLOWED = True",
    )

    forbidden_present = tuple(
        marker
        for marker in forbidden_markers
        if marker in source
    )

    if forbidden_present:
        raise AssertionError(
            "OLA-075 contains forbidden execution "
            f"logic: {forbidden_present}"
        )

    result = {
        "schema_version": "OLA-075",
        "engine_id": "OLA-075",
        "status": "passed",
        "canonical_operator_entry_point_installed": True,
        "canonical_operator_command": (
            "py run_oracle_live_shadow_CONTINUOUS.py"
        ),
        "certified_ola074_guarded_launcher_required": True,
        "exact_guarded_schema_enforced": True,
        "exact_guarded_engine_enforced": True,
        "guarded_main_callable_required": True,
        "guarded_launcher_called_once": True,
        "guarded_exit_code_propagated": True,
        "operator_keyboard_interrupt_preserved": True,
        "production_runtime_started_during_test": False,
        "signal_handlers_modified": False,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    print(
        "[PASS] OLA-075 Oracle Continuous "
        "Operator Entry Point"
    )

    print(result)


if __name__ == "__main__":
    main()
