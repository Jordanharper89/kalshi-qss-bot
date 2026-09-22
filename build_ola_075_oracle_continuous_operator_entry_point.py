from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

ENTRY_POINT_FILE = (
    ROOT
    / "run_oracle_live_shadow_CONTINUOUS.py"
)

TEST_FILE = (
    ROOT
    / "test_ola_075_oracle_continuous_operator_entry_point.py"
)


ENTRY_POINT_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import importlib.util
    import sys
    from pathlib import Path
    from types import ModuleType
    from typing import Callable


    SCHEMA_VERSION = "OLA-075"
    ENGINE_ID = "OLA-075"

    READ_ONLY = True
    EXECUTION_ALLOWED = False
    ORDER_PLACEMENT_ALLOWED = False
    FUNDS_MOVEMENT_ALLOWED = False
    PORTFOLIO_MUTATION_ALLOWED = False

    REQUIRED_GUARDED_SCHEMA_VERSION = "OLA-074"
    REQUIRED_GUARDED_ENGINE_ID = "OLA-074"

    ROOT = Path(__file__).resolve().parent

    GUARDED_LAUNCHER_FILE = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
    )


    class OracleContinuousOperatorEntryPointError(
        RuntimeError
    ):
        pass


    class OracleGuardedLauncherNotFoundError(
        OracleContinuousOperatorEntryPointError
    ):
        pass


    class OracleGuardedLauncherContractError(
        OracleContinuousOperatorEntryPointError
    ):
        pass


    def _load_module_from_path(
        path: Path,
        module_name: str,
    ) -> ModuleType:
        if not path.is_file():
            raise OracleGuardedLauncherNotFoundError(
                "Certified OLA-074 guarded launcher "
                f"was not found: {path}"
            )

        specification = (
            importlib.util.spec_from_file_location(
                module_name,
                path,
            )
        )

        if (
            specification is None
            or specification.loader is None
        ):
            raise OracleGuardedLauncherContractError(
                "Could not create an import specification "
                f"for guarded launcher: {path}"
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


    def _validate_read_only_boundary() -> None:
        if READ_ONLY is not True:
            raise OracleContinuousOperatorEntryPointError(
                "Oracle operator entry point must remain "
                "read-only"
            )

        forbidden_flags = {
            "execution_allowed": EXECUTION_ALLOWED,
            "order_placement_allowed": (
                ORDER_PLACEMENT_ALLOWED
            ),
            "funds_movement_allowed": (
                FUNDS_MOVEMENT_ALLOWED
            ),
            "portfolio_mutation_allowed": (
                PORTFOLIO_MUTATION_ALLOWED
            ),
        }

        enabled_forbidden_flags = tuple(
            flag_name
            for flag_name, flag_value
            in forbidden_flags.items()
            if flag_value is not False
        )

        if enabled_forbidden_flags:
            raise OracleContinuousOperatorEntryPointError(
                "Oracle execution boundary violation: "
                f"{enabled_forbidden_flags}"
            )


    def _load_guarded_launcher() -> ModuleType:
        module = _load_module_from_path(
            GUARDED_LAUNCHER_FILE,
            "ola075_required_ola074_guarded_launcher",
        )

        actual_schema_version = getattr(
            module,
            "SCHEMA_VERSION",
            None,
        )

        actual_engine_id = getattr(
            module,
            "ENGINE_ID",
            None,
        )

        if (
            actual_schema_version
            != REQUIRED_GUARDED_SCHEMA_VERSION
        ):
            raise OracleGuardedLauncherContractError(
                "Guarded launcher schema mismatch. "
                f"Expected {REQUIRED_GUARDED_SCHEMA_VERSION}, "
                f"received {actual_schema_version!r}"
            )

        if (
            actual_engine_id
            != REQUIRED_GUARDED_ENGINE_ID
        ):
            raise OracleGuardedLauncherContractError(
                "Guarded launcher engine mismatch. "
                f"Expected {REQUIRED_GUARDED_ENGINE_ID}, "
                f"received {actual_engine_id!r}"
            )

        guarded_main = getattr(
            module,
            "main",
            None,
        )

        if not callable(
            guarded_main
        ):
            raise OracleGuardedLauncherContractError(
                "Certified OLA-074 guarded launcher "
                "does not expose callable main()"
            )

        guarded_read_only = getattr(
            module,
            "READ_ONLY",
            True,
        )

        guarded_execution_allowed = getattr(
            module,
            "EXECUTION_ALLOWED",
            False,
        )

        if guarded_read_only is not True:
            raise OracleGuardedLauncherContractError(
                "Certified guarded launcher is not "
                "read-only"
            )

        if guarded_execution_allowed is not False:
            raise OracleGuardedLauncherContractError(
                "Certified guarded launcher permits "
                "execution"
            )

        return module


    def _normalize_exit_code(
        value: object,
    ) -> int:
        if value is None:
            return 0

        if isinstance(
            value,
            bool,
        ):
            return 0 if value else 1

        if isinstance(
            value,
            int,
        ):
            return value

        raise OracleGuardedLauncherContractError(
            "OLA-074 guarded launcher returned an "
            "unsupported exit result: "
            f"{type(value).__name__}"
        )


    def main() -> int:
        print("========================================")
        print(" ORACLE CONTINUOUS OPERATOR ENTRY POINT")
        print(" OLA-075 CANONICAL NONSTOP START COMMAND")
        print(" GUARDED READ-ONLY LIVE SHADOW")
        print("========================================")

        _validate_read_only_boundary()

        print(
            "[OK] Read-only operator boundary frozen"
        )

        guarded_launcher = (
            _load_guarded_launcher()
        )

        print(
            "[OK] Certified OLA-074 guarded "
            "launcher resolved"
        )

        print(
            "[START] Delegating to guarded "
            "continuous production runtime"
        )

        guarded_main: Callable[[], object] = getattr(
            guarded_launcher,
            "main",
        )

        result = guarded_main()

        exit_code = _normalize_exit_code(
            result
        )

        print(
            "[STOP] Guarded continuous runtime returned"
        )

        print(
            "[INFO] Guarded launcher exit code:",
            exit_code,
        )

        return exit_code


    if __name__ == "__main__":
        try:
            sys.exit(
                main()
            )

        except KeyboardInterrupt:
            print()
            print(
                "[STOP] Oracle continuous runtime "
                "interrupted by operator"
            )

            sys.exit(130)

        except Exception as exc:
            print()
            print(
                "[ERROR]",
                type(exc).__name__ + ":",
                str(exc),
            )

            sys.exit(1)
    '''
).lstrip()


TEST_SOURCE = dedent(
    r'''
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
    '''
).lstrip()


def write_full_replacement(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def validate_installation() -> None:
    entry_source = ENTRY_POINT_FILE.read_text(
        encoding="utf-8"
    )

    test_source = TEST_FILE.read_text(
        encoding="utf-8"
    )

    entry_required_markers = (
        'SCHEMA_VERSION = "OLA-075"',
        'ENGINE_ID = "OLA-075"',
        'REQUIRED_GUARDED_SCHEMA_VERSION = "OLA-074"',
        "run_oracle_live_shadow_CONTINUOUS_GUARDED.py",
        "_validate_read_only_boundary",
        "_load_guarded_launcher",
        "_normalize_exit_code",
        "except KeyboardInterrupt:",
        "sys.exit(130)",
    )

    test_required_markers = (
        "OLA-075 OPERATOR ENTRY POINT TEST",
        "NO REAL CONTINUOUS SERVICE START",
        "FakeGuardedLauncher",
        "Successful guarded delegation",
        "Operator interrupt propagation",
        "Exact OLA-074 dependency",
        "production_runtime_started_during_test",
        "[PASS] OLA-075",
    )

    missing_entry_markers = tuple(
        marker
        for marker in entry_required_markers
        if marker not in entry_source
    )

    missing_test_markers = tuple(
        marker
        for marker in test_required_markers
        if marker not in test_source
    )

    if missing_entry_markers:
        raise RuntimeError(
            "OLA-075 operator entry point is incomplete. "
            f"Missing markers: {missing_entry_markers}"
        )

    if missing_test_markers:
        raise RuntimeError(
            "OLA-075 test is incomplete. "
            f"Missing markers: {missing_test_markers}"
        )

    forbidden_entry_markers = (
        "requests.post(",
        "place_order(",
        "submit_order(",
        "execute_trade(",
        "ORDER_PLACEMENT_ALLOWED = True",
        "FUNDS_MOVEMENT_ALLOWED = True",
        "PORTFOLIO_MUTATION_ALLOWED = True",
    )

    forbidden_present = tuple(
        marker
        for marker in forbidden_entry_markers
        if marker in entry_source
    )

    if forbidden_present:
        raise RuntimeError(
            "OLA-075 contains forbidden execution logic: "
            f"{forbidden_present}"
        )

    compile(
        entry_source,
        str(ENTRY_POINT_FILE),
        "exec",
    )

    compile(
        test_source,
        str(TEST_FILE),
        "exec",
    )

    print(
        "[OK] Canonical continuous operator "
        "entry point installed"
    )

    print(
        "[OK] Exact OLA-074 guarded dependency frozen"
    )

    print(
        "[OK] Single guarded-launch delegation frozen"
    )

    print(
        "[OK] Guarded exit-code propagation frozen"
    )

    print(
        "[OK] Operator Ctrl+C behavior preserved"
    )

    print(
        "[OK] Oracle read-only boundary frozen"
    )

    print(
        "[OK] Deterministic test uses fake launcher only"
    )

    print(
        "[OK] No real continuous runtime starts in test"
    )

    print(
        "[OK] Python syntax compilation passed"
    )


def main() -> None:
    print("========================================")
    print(" OLA-075 INSTALLER")
    print(" ORACLE CONTINUOUS OPERATOR ENTRY POINT")
    print(" CANONICAL NONSTOP START COMMAND")
    print("========================================")

    write_full_replacement(
        ENTRY_POINT_FILE,
        ENTRY_POINT_SOURCE,
    )

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-075 Oracle continuous "
        "operator entry point installed"
    )

    print()
    print("Run:")
    print(
        "py "
        "test_ola_075_oracle_continuous_"
        "operator_entry_point.py"
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print()
        print(
            f"[ERROR] {type(exc).__name__}: {exc}"
        )

        sys.exit(1)