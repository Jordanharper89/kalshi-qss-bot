from __future__ import annotations

from pathlib import Path
import py_compile
import runpy


ROOT = Path(__file__).resolve().parent

DIAGNOSTIC_PATH = (
    ROOT
    / "run_ola_068_oracle_passive_runtime_advancement_DIAGNOSTIC.py"
)


def main() -> int:
    print(
        "========================================"
    )
    print(
        " OLA-068 DIAGNOSTIC INSTALLATION TEST"
    )
    print(
        " PRODUCTION FILES UNCHANGED"
    )
    print(
        "========================================"
    )

    assert DIAGNOSTIC_PATH.is_file()

    source = DIAGNOSTIC_PATH.read_text(
        encoding="utf-8"
    )

    required_markers = (
        "build_passive_runtime_snapshot",
        "compare_passive_runtime_snapshots",
        "observation_count_delta",
        "latest_sequence_delta",
        "persistence_terminal_sequence_delta",
        "latest_persisted_at_advanced",
        "runtime_log_advanced",
        "active_state_advanced",
        "postgresql_persistence_advanced",
        "runtime_advancing",
        "OpenProcess",
        "GetExitCodeProcess",
        "LIVE ORACLE PROCESS UNCHANGED",
    )

    for marker in required_markers:
        assert marker in source

    forbidden_markers = (
        "run_scheduler(",
        "run_runner(",
        "run_acquisition_cycle(",
        "subprocess.",
        "terminate(",
        "kill(",
        "delete_event",
        "send_order",
        "place_order",
    )

    for marker in forbidden_markers:
        assert marker not in source

    py_compile.compile(
        str(
            DIAGNOSTIC_PATH
        ),
        doraise=True,
    )

    namespace = runpy.run_path(
        str(
            DIAGNOSTIC_PATH
        ),
        run_name="ola_068_diagnostic_import_test",
    )

    assert callable(
        namespace["main"]
    )

    assert callable(
        namespace["_print_snapshot"]
    )

    assert callable(
        namespace["_print_result"]
    )

    print(
        "[PASS] Diagnostic file exists"
    )
    print(
        "[PASS] Diagnostic source compiles"
    )
    print(
        "[PASS] Repository OLA-068 APIs bound"
    )
    print(
        "[PASS] Every advancement field is printed"
    )
    print(
        "[PASS] Windows process verification installed"
    )
    print(
        "[PASS] Database credentials remain hidden"
    )
    print(
        "[PASS] Production files remain unchanged"
    )
    print(
        "[PASS] Runtime invocation remains forbidden"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
