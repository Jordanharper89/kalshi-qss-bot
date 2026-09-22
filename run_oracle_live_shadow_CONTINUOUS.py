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
