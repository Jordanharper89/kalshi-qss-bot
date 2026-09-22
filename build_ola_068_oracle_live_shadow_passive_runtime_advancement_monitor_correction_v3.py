from __future__ import annotations

from pathlib import Path
import py_compile


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_live_shadow_passive_runtime_advancement_monitor.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_068_oracle_postgresql_canonical_advancement_correction_v3.py"
)


OLD_DECISION = """    runtime_advancing = (
        postgresql_persistence_advanced
        and (
            runtime_log_advanced
            or active_state_advanced
        )
    )
"""


NEW_DECISION = """    # Canonical continuous-runtime advancement is established by
    # PostgreSQL persistence. The guarded continuous process persists
    # canonical observations every cycle without necessarily rewriting
    # the historical launch log or state/current.json.
    #
    # Runtime-log and active-state movement remain captured as supporting
    # evidence, but neither filesystem artifact is mandatory.
    runtime_advancing = (
        postgresql_persistence_advanced
    )
"""


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_passive_runtime_advancement_monitor import (
    OraclePassiveRuntimeSnapshot,
    compare_passive_runtime_snapshots,
)


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_live_shadow_passive_runtime_advancement_monitor.py"
)


def _snapshot(
    *,
    captured_at: datetime,
    observation_count: int,
    latest_sequence_number: int,
    persistence_terminal_sequence: int,
    latest_persisted_at: datetime,
) -> OraclePassiveRuntimeSnapshot:
    return OraclePassiveRuntimeSnapshot(
        schema_version="OLA-068-SNAPSHOT",
        engine_id="OLA-068",
        captured_at=captured_at,
        observation_count=observation_count,
        latest_sequence_number=latest_sequence_number,
        persistence_terminal_sequence=(
            persistence_terminal_sequence
        ),
        latest_persisted_at=latest_persisted_at,
        newest_runtime_log_path=(
            "runtime/oracle_live_shadow/logs/"
            "historical-log.json"
        ),
        newest_runtime_log_modified_at=captured_at,
        newest_runtime_log_size_bytes=5638,
        newest_runtime_log_sha256="a" * 64,
        active_state_path=(
            "runtime/oracle_live_shadow/state/current.json"
        ),
        active_state_modified_at=captured_at,
        active_state_size_bytes=1190,
        active_state_sha256="b" * 64,
        snapshot_hash="c" * 64,
    )


def main() -> int:
    print(
        "========================================"
    )
    print(
        " OLA-068 CORRECTION V3 TEST"
    )
    print(
        " POSTGRESQL CANONICAL ADVANCEMENT"
    )
    print(
        " FILESYSTEM EVIDENCE SUPPORTING ONLY"
    )
    print(
        "========================================"
    )

    source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    forbidden_block = """    runtime_advancing = (
        postgresql_persistence_advanced
        and (
            runtime_log_advanced
            or active_state_advanced
        )
    )
"""

    required_block = """    runtime_advancing = (
        postgresql_persistence_advanced
    )
"""

    assert forbidden_block not in source
    assert required_block in source

    base_time = datetime(
        2026,
        7,
        19,
        15,
        59,
        21,
        tzinfo=timezone.utc,
    )

    before = _snapshot(
        captured_at=base_time,
        observation_count=18974,
        latest_sequence_number=18974,
        persistence_terminal_sequence=18974,
        latest_persisted_at=base_time,
    )

    after = _snapshot(
        captured_at=(
            base_time
            + timedelta(seconds=30)
        ),
        observation_count=18999,
        latest_sequence_number=18999,
        persistence_terminal_sequence=18999,
        latest_persisted_at=(
            base_time
            + timedelta(seconds=29)
        ),
    )

    record = compare_passive_runtime_snapshots(
        before=before,
        after=after,
        observation_window_seconds=30.0,
        evaluated_at=(
            base_time
            + timedelta(seconds=31)
        ),
    )

    assert record.observation_count_delta == 25
    assert record.latest_sequence_delta == 25

    assert (
        record.persistence_terminal_sequence_delta
        == 25
    )

    assert (
        record.latest_persisted_at_advanced
        is True
    )

    assert record.runtime_log_advanced is False
    assert record.active_state_advanced is False

    assert (
        record.postgresql_persistence_advanced
        is True
    )

    assert record.runtime_advancing is True
    assert record.status == "advancing"

    assert (
        record.existing_runtime_observed_only
        is True
    )

    assert record.acquisition_cycle_invoked is False
    assert record.scheduler_invoked is False
    assert record.runner_invoked is False
    assert record.read_only is True
    assert record.execution_allowed is False

    print(
        "[PASS] Observation count advancement required"
    )
    print(
        "[PASS] Latest sequence advancement required"
    )
    print(
        "[PASS] Persistence terminal advancement required"
    )
    print(
        "[PASS] Latest persisted timestamp advancement required"
    )
    print(
        "[PASS] Unchanged runtime log accepted"
    )
    print(
        "[PASS] Unchanged active state accepted"
    )
    print(
        "[PASS] PostgreSQL persistence is canonical"
    )
    print(
        "[PASS] Runtime status is advancing"
    )
    print(
        "[PASS] Passive observation preserved"
    )
    print(
        "[PASS] Oracle remains read-only"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
'''


def main() -> int:
    print(
        "========================================"
    )
    print(
        " OLA-068 PRODUCTION CORRECTION V3"
    )
    print(
        " POSTGRESQL CANONICAL ADVANCEMENT"
    )
    print(
        " FILESYSTEM EVIDENCE SUPPORTING ONLY"
    )
    print(
        "========================================"
    )

    if not PRODUCTION_PATH.is_file():
        raise RuntimeError(
            f"Production module not found: "
            f"{PRODUCTION_PATH}"
        )

    production_source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    old_count = production_source.count(
        OLD_DECISION
    )

    new_count = production_source.count(
        NEW_DECISION
    )

    if old_count == 1:
        corrected_source = production_source.replace(
            OLD_DECISION,
            NEW_DECISION,
            1,
        )
    elif (
        old_count == 0
        and new_count == 1
    ):
        corrected_source = production_source

        print(
            "[INFO] Canonical PostgreSQL decision "
            "already installed"
        )
    else:
        raise RuntimeError(
            "OLA-068 runtime decision contract did not "
            "match the expected repository state. "
            f"old_count={old_count}, "
            f"new_count={new_count}"
        )

    if OLD_DECISION in corrected_source:
        raise RuntimeError(
            "Faulty filesystem-dependent decision remains"
        )

    if corrected_source.count(
        NEW_DECISION
    ) != 1:
        raise RuntimeError(
            "Canonical PostgreSQL decision was not "
            "installed exactly once"
        )

    py_compile.compile(
        str(PRODUCTION_PATH),
        doraise=True,
    )

    PRODUCTION_PATH.write_text(
        corrected_source,
        encoding="utf-8",
        newline="\n",
    )

    py_compile.compile(
        str(PRODUCTION_PATH),
        doraise=True,
    )

    TEST_PATH.write_text(
        TEST_SOURCE,
        encoding="utf-8",
        newline="\n",
    )

    py_compile.compile(
        str(TEST_PATH),
        doraise=True,
    )

    print(
        f"[OK] FULL REPLACEMENT: {PRODUCTION_PATH}"
    )
    print(
        f"[OK] FULL REPLACEMENT: {TEST_PATH}"
    )
    print(
        "[OK] PostgreSQL persistence made canonical"
    )
    print(
        "[OK] Mandatory runtime-log movement removed"
    )
    print(
        "[OK] Mandatory active-state movement removed"
    )
    print(
        "[OK] Filesystem evidence fields preserved"
    )
    print(
        "[OK] Passive observation preserved"
    )
    print(
        "[OK] Runtime invocation remains forbidden"
    )
    print(
        "[OK] Oracle remains read-only"
    )
    print(
        "[DONE] OLA-068 production correction V3 installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )