from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent

TEST_FILE = (
    REPOSITORY_ROOT
    / "test_ola_071_oracle_corrected_production_restart_verification_gate.py"
)


OLD_GRAPH_CALL = """        graph = build_real_oracle_shadow_graph(
            runtime_root=ROOT.resolve(),
            environment=environment,
            service_tick_interval_seconds=0,
        )
"""


NEW_GRAPH_CALL = """        graph = build_real_oracle_shadow_graph(
            runtime_root=ROOT.resolve(),
            environment=environment,

            # OLA-071 correction V2:
            # ShadowPollingPolicy requires a strictly positive
            # base polling interval. One second preserves the
            # canonical production cadence contract while keeping
            # this verification bounded to exactly three cycles.
            service_tick_interval_seconds=1,
        )
"""


def install_correction() -> None:
    if not TEST_FILE.exists():
        raise RuntimeError(
            f"OLA-071 test file not found: {TEST_FILE}"
        )

    existing_source = TEST_FILE.read_text(
        encoding="utf-8"
    )

    if NEW_GRAPH_CALL in existing_source:
        corrected_source = existing_source
        print(
            "[OK] OLA-071 positive cadence correction "
            "already present"
        )
    else:
        if OLD_GRAPH_CALL not in existing_source:
            raise RuntimeError(
                "Could not locate the exact OLA-071 "
                "production graph construction block."
            )

        corrected_source = existing_source.replace(
            OLD_GRAPH_CALL,
            NEW_GRAPH_CALL,
            1,
        )

    TEST_FILE.write_text(
        corrected_source,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] FULL REPLACEMENT: {TEST_FILE}"
    )


def validate_installation() -> None:
    installed_source = TEST_FILE.read_text(
        encoding="utf-8"
    )

    required_markers = (
        'SCHEMA_VERSION = "OLA-071"',
        "build_real_oracle_shadow_graph",
        "service_tick_interval_seconds=1",
        '"max_iterations": 3',
        "production_live_shadow_persistent_service_activator",
        "observation_delta > 0",
        "sequence_delta > 0",
        "persistence_delta > 0",
        "background_process_left_running",
        "[PASS] OLA-071",
    )

    missing_markers = [
        marker
        for marker in required_markers
        if marker not in installed_source
    ]

    if missing_markers:
        raise RuntimeError(
            "OLA-071 correction installation is incomplete. "
            f"Missing markers: {missing_markers}"
        )

    forbidden_markers = (
        "service_tick_interval_seconds=0",
    )

    present_forbidden_markers = [
        marker
        for marker in forbidden_markers
        if marker in installed_source
    ]

    if present_forbidden_markers:
        raise RuntimeError(
            "OLA-071 still contains an invalid zero cadence: "
            f"{present_forbidden_markers}"
        )

    print(
        "[OK] Positive polling cadence verified: "
        "1 second"
    )

    print(
        "[OK] Bounded iteration count verified: "
        "3 cycles"
    )

    print(
        "[OK] PostgreSQL advancement assertions preserved"
    )

    print(
        "[OK] Read-only production boundaries preserved"
    )


def main() -> None:
    print("========================================")
    print(" OLA-071 PRODUCTION CORRECTION V2")
    print(" POSITIVE BOUNDED POLLING CADENCE")
    print(" THREE-CYCLE RESTART VERIFICATION")
    print("========================================")

    install_correction()
    validate_installation()

    print()
    print(
        "[DONE] OLA-071 positive cadence production "
        "correction V2 installed"
    )

    print()
    print("Run:")
    print(
        "py "
        "test_ola_071_oracle_corrected_"
        "production_restart_verification_gate.py"
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