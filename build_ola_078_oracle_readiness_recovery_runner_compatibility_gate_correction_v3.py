from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

TEST_PATH = (
    ROOT
    / "test_ola_078_oracle_readiness_recovery_runner_compatibility_gate.py"
)


OLD_BLOCK = '''    class WrongReadinessRecord:
        schema_version = "OLA-018"
        engine_id = "OLA-018"
        checked_at = checked_at
        evaluated_at = evaluated_at
        readiness_status = "passed"
        live_shadow_cycle_entry_ready = True
        shadow_mode = True
        alerts_allowed = False
        qseries_intake_allowed = False
        read_only = True
        execution_allowed = False

    try:
        runner._validate_readiness(
            readiness=WrongReadinessRecord(),
            supplied_checked_at=checked_at,
            supplied_evaluated_at=evaluated_at,
        )
'''


NEW_BLOCK = '''    class WrongReadinessRecord:
        schema_version = "OLA-018"
        engine_id = "OLA-018"
        readiness_status = "passed"
        live_shadow_cycle_entry_ready = True
        shadow_mode = True
        alerts_allowed = False
        qseries_intake_allowed = False
        read_only = True
        execution_allowed = False

        def __init__(
            self,
            *,
            record_checked_at,
            record_evaluated_at,
        ) -> None:
            self.checked_at = record_checked_at
            self.evaluated_at = record_evaluated_at

    wrong_readiness = WrongReadinessRecord(
        record_checked_at=checked_at,
        record_evaluated_at=evaluated_at,
    )

    try:
        runner._validate_readiness(
            readiness=wrong_readiness,
            supplied_checked_at=checked_at,
            supplied_evaluated_at=evaluated_at,
        )
'''


def read_current_test_source() -> str:
    if not TEST_PATH.exists():
        raise FileNotFoundError(
            f"Missing OLA-078 test file: {TEST_PATH}"
        )

    source = TEST_PATH.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        "OLA-078 RECOVERY/RUNNER COMPATIBILITY",
        "CANONICAL OLA-018 READINESS RECORD",
        "KalshiLiveReadReadinessRecord",
        "Recovered readiness passed OLA-023 validation",
        "Strict runner rejects wrong record type",
    )

    for token in required_tokens:
        if token not in source:
            raise RuntimeError(
                "Expected OLA-078 V2 test contract missing: "
                f"{token}"
            )

    old_count = source.count(
        OLD_BLOCK
    )

    if old_count != 1:
        raise RuntimeError(
            "Expected exactly one invalid wrong-record fixture; "
            f"found {old_count}. Test file was not changed."
        )

    return source


def build_corrected_test_source(
    current_source: str,
) -> str:
    corrected_source = current_source.replace(
        OLD_BLOCK,
        NEW_BLOCK,
        1,
    )

    if corrected_source == current_source:
        raise RuntimeError(
            "OLA-078 V3 correction produced no change"
        )

    if OLD_BLOCK in corrected_source:
        raise RuntimeError(
            "Invalid class-scope fixture remains after correction"
        )

    if corrected_source.count(
        NEW_BLOCK
    ) != 1:
        raise RuntimeError(
            "Corrected wrong-record fixture was not installed "
            "exactly once"
        )

    forbidden_stale_tokens = (
        "checked_at = checked_at",
        "evaluated_at = evaluated_at",
        "readiness=WrongReadinessRecord()",
    )

    for token in forbidden_stale_tokens:
        if token in corrected_source:
            raise RuntimeError(
                "Stale invalid fixture token remains: "
                f"{token}"
            )

    required_new_tokens = (
        "def __init__(",
        "record_checked_at=checked_at",
        "record_evaluated_at=evaluated_at",
        "readiness=wrong_readiness",
    )

    for token in required_new_tokens:
        if token not in corrected_source:
            raise RuntimeError(
                "Corrected fixture token missing: "
                f"{token}"
            )

    compile(
        corrected_source,
        str(TEST_PATH),
        "exec",
    )

    return corrected_source


def write_full_replacement(
    path: Path,
    source: str,
) -> None:
    temporary_path = path.with_name(
        path.name + ".ola078_v3.tmp"
    )

    temporary_path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    written_source = temporary_path.read_text(
        encoding="utf-8"
    )

    compile(
        written_source,
        str(path),
        "exec",
    )

    temporary_path.replace(
        path
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def verify_installed_test() -> None:
    source = TEST_PATH.read_text(
        encoding="utf-8"
    )

    assert "checked_at = checked_at" not in source
    assert "evaluated_at = evaluated_at" not in source
    assert "readiness=WrongReadinessRecord()" not in source

    assert "record_checked_at=checked_at" in source
    assert "record_evaluated_at=evaluated_at" in source
    assert "readiness=wrong_readiness" in source

    compile(
        source,
        str(TEST_PATH),
        "exec",
    )


def main() -> int:
    print("========================================")
    print(" OLA-078 TEST CORRECTION V3")
    print(" WRONG-RECORD FIXTURE SCOPE CORRECTION")
    print(" PRODUCTION FILES UNCHANGED")
    print("========================================")

    current_source = read_current_test_source()

    corrected_source = build_corrected_test_source(
        current_source
    )

    write_full_replacement(
        TEST_PATH,
        corrected_source,
    )

    verify_installed_test()

    print("[OK] Invalid class-scope variable lookup removed")
    print("[OK] Wrong readiness record now uses __init__")
    print("[OK] checked_at explicitly supplied to fixture")
    print("[OK] evaluated_at explicitly supplied to fixture")
    print("[OK] Wrong record-type rejection test preserved")
    print("[OK] Canonical recovery test preserved")
    print("[OK] Strict OLA-023 validation preserved")
    print("[OK] OLA-077 production correction preserved")
    print("[OK] Production files unchanged")
    print("[OK] Oracle read-only boundary unchanged")
    print("[OK] No real continuous service started")

    print(
        "\n[DONE] OLA-078 test correction V3 installed"
    )

    print("\nRun:")
    print(
        "py test_ola_078_"
        "oracle_readiness_recovery_runner_compatibility_gate.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )