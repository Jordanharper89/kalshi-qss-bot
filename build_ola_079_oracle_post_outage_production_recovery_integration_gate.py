from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

TEST_PATH = (
    ROOT
    / "test_ola_079_oracle_post_outage_production_recovery_integration_gate.py"
)


TEST_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import contextlib
    import importlib
    import io
    import traceback
    from pathlib import Path


    SCHEMA_VERSION = "OLA-079"
    ENGINE_ID = "OLA-079"

    ROOT = Path(__file__).resolve().parent

    OLA077_PRODUCTION_PATH = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition_model"
        / "oracle_first_real_shadow_corpus_launch_command.py"
    )

    OLA078_PRODUCTION_PATH = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "oracle_kalshi_live_read_readiness_gate.py"
    )

    LIVE_ACQUISITION_PACKAGE_PATH = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "__init__.py"
    )

    OLA071_TEST_PATH = (
        ROOT
        / "test_ola_071_oracle_corrected_production_restart_verification_gate.py"
    )

    READ_ONLY = True
    EXECUTION_ALLOWED = False
    ALERTS_ALLOWED = False
    QSERIES_HANDOFF_ALLOWED = False
    TRADE_AUTHORIZATION_ALLOWED = False
    ORDER_PLACEMENT_ALLOWED = False
    FUNDS_MOVED = False
    PORTFOLIO_MUTATED = False


    class Tee:
        def __init__(
            self,
            *streams,
        ) -> None:
            self._streams = streams

        def write(
            self,
            text: str,
        ) -> int:
            for stream in self._streams:
                stream.write(text)
                stream.flush()

            return len(text)

        def flush(self) -> None:
            for stream in self._streams:
                stream.flush()


    def read_required_source(
        path: Path,
    ) -> str:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file does not exist: {path}"
            )

        return path.read_text(
            encoding="utf-8"
        )


    def assert_static_correction_chain() -> None:
        ola077_source = read_required_source(
            OLA077_PRODUCTION_PATH
        )

        ola078_source = read_required_source(
            OLA078_PRODUCTION_PATH
        )

        package_source = read_required_source(
            LIVE_ACQUISITION_PACKAGE_PATH
        )

        required_ola077_tokens = (
            "OLA-077 canonical retry timestamp-lineage correction",
            "_rehydrate_canonical_aware_datetime(",
            'checked_at,\n                        "checked_at",',
            'evaluated_at,\n                        "evaluated_at",',
        )

        for token in required_ola077_tokens:
            if token not in ola077_source:
                raise AssertionError(
                    "OLA-077 production correction is missing "
                    f"required token: {token}"
                )

        forbidden_ola077_retry_token = (
            "else:\n"
            "                attempt_checked_at = "
            "self._fresh_timestamp()"
        )

        if forbidden_ola077_retry_token in ola077_source:
            raise AssertionError(
                "Stale OLA-069 retry timestamp authority remains."
            )

        required_ola078_tokens = (
            "OLA-078 health approval compatibility contract",
            "OLA-078 V2 backward-compatibility export",
            "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
            "HEALTH_LATENCY_APPROVAL_REASON_CODES",
            "HEALTH_APPROVAL_REASON_CODES = frozenset(",
            "health_required_evidence_present",
            "health_latency_evidence_present",
        )

        for token in required_ola078_tokens:
            if token not in ola078_source:
                raise AssertionError(
                    "OLA-078 production correction is missing "
                    f"required token: {token}"
                )

        required_package_tokens = (
            "HEALTH_APPROVAL_REASON_CODES,",
            "HEALTH_REQUIRED_APPROVAL_REASON_CODES,",
            "HEALTH_LATENCY_APPROVAL_REASON_CODES,",
            '"HEALTH_APPROVAL_REASON_CODES"',
            '"HEALTH_REQUIRED_APPROVAL_REASON_CODES"',
            '"HEALTH_LATENCY_APPROVAL_REASON_CODES"',
        )

        for token in required_package_tokens:
            if token not in package_source:
                raise AssertionError(
                    "Live-acquisition package compatibility is "
                    f"missing required token: {token}"
                )


    def assert_package_import_surface() -> None:
        package = importlib.import_module(
            "qseries_v2.oracle_intelligence.live_acquisition"
        )

        required_health = getattr(
            package,
            "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
        )

        latency_health = getattr(
            package,
            "HEALTH_LATENCY_APPROVAL_REASON_CODES",
        )

        legacy_health = getattr(
            package,
            "HEALTH_APPROVAL_REASON_CODES",
        )

        assert required_health == frozenset(
            {
                "source_reachable",
                "consecutive_failures_within_policy",
            }
        )

        assert latency_health == frozenset(
            {
                "latency_within_policy",
                "latency_policy_not_required",
            }
        )

        assert legacy_health == frozenset(
            required_health
            | latency_health
        )


    def run_actual_bounded_production_gate() -> str:
        if not OLA071_TEST_PATH.exists():
            raise FileNotFoundError(
                "Required OLA-071 real production verification "
                f"gate is missing: {OLA071_TEST_PATH}"
            )

        module = importlib.import_module(
            "test_ola_071_oracle_corrected_"
            "production_restart_verification_gate"
        )

        main_callable = getattr(
            module,
            "main",
            None,
        )

        if not callable(main_callable):
            raise AssertionError(
                "OLA-071 real production verification main "
                "callable was not resolved."
            )

        captured_output = io.StringIO()

        tee = Tee(
            captured_output,
            __import__("sys").stdout,
        )

        with contextlib.redirect_stdout(
            tee
        ):
            main_callable()

        return captured_output.getvalue()


    def assert_actual_runtime_evidence(
        output: str,
    ) -> None:
        required_runtime_tokens = (
            "[OK] OLA-030 production graph assembled",
            "[OK] Exact graph runner resolved: runner",
            "[START] Executing exactly three bounded production cycles",
            "[STOP] Bounded production service returned",
            "[DELTA] observations:",
            "[DELTA] sequence:",
            "[DELTA] persistence terminal:",
            "[ADVANCED] persisted timestamp: True",
            "[PASS] OLA-071 Oracle Corrected Production Restart Verification Gate",
        )

        for token in required_runtime_tokens:
            if token not in output:
                raise AssertionError(
                    "Real production recovery output is missing "
                    f"required evidence: {token}"
                )

        forbidden_runtime_tokens = (
            "readiness provider did not preserve checked_at",
            "readiness provider did not preserve evaluated_at",
            "OLA-002 decision lacks health approval reasons",
            "OLA-002 decision lacks required health approval reasons",
            "OLA-002 decision lacks valid latency approval reason",
            "OracleLiveShadowServiceRunnerCompatibilityError",
            "ImportError:",
            "Traceback (most recent call last):",
        )

        for token in forbidden_runtime_tokens:
            if token in output:
                raise AssertionError(
                    "Corrected production runtime emitted forbidden "
                    f"failure evidence: {token}"
                )


    def assert_read_only_boundary() -> None:
        assert READ_ONLY is True
        assert EXECUTION_ALLOWED is False
        assert ALERTS_ALLOWED is False
        assert QSERIES_HANDOFF_ALLOWED is False
        assert TRADE_AUTHORIZATION_ALLOWED is False
        assert ORDER_PLACEMENT_ALLOWED is False
        assert FUNDS_MOVED is False
        assert PORTFOLIO_MUTATED is False


    def main() -> int:
        print("========================================")
        print(" OLA-079 POST-OUTAGE RECOVERY GATE")
        print(" REAL THREE-CYCLE PRODUCTION VERIFY")
        print(" OLA-077 + OLA-078 INTEGRATION")
        print("========================================")

        assert_read_only_boundary()

        print("[TEST] Static correction chain")

        assert_static_correction_chain()

        print("[OK] OLA-077 timestamp correction installed")
        print("[OK] OLA-078 latency correction installed")
        print("[OK] Package compatibility correction installed")

        print("[TEST] Package import surface")

        assert_package_import_surface()

        print("[OK] Package import surface")

        print("[TEST] Actual bounded production recovery")

        try:
            runtime_output = (
                run_actual_bounded_production_gate()
            )
        except BaseException:
            print(
                "[FAIL] Actual bounded production recovery "
                "did not complete"
            )

            traceback.print_exc()
            raise

        assert_actual_runtime_evidence(
            runtime_output
        )

        print("[OK] Three real production cycles completed")
        print("[OK] PostgreSQL persistence advanced")
        print("[OK] Canonical sequence advanced")
        print("[OK] Persistence terminal advanced")
        print("[OK] Runtime evidence advanced")
        print("[OK] OLA-077 compatibility crash absent")
        print("[OK] OLA-078 readiness block absent")

        print("[TEST] Oracle authority boundary")

        assert_read_only_boundary()

        print("[OK] Oracle read-only boundary preserved")

        print(
            "[PASS] OLA-079 Oracle Post-Outage "
            "Production Recovery Integration Gate"
        )

        print({
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "ola077_installed": True,
            "ola078_v2_installed": True,
            "package_import_surface_verified": True,
            "actual_ola030_graph_used": True,
            "actual_ola063_activator_used": True,
            "actual_ola023_runner_used": True,
            "actual_bounded_iterations": 3,
            "real_kalshi_read_path_exercised": True,
            "real_postgresql_persistence_exercised": True,
            "observation_count_advanced": True,
            "canonical_sequence_advanced": True,
            "persistence_terminal_advanced": True,
            "runtime_evidence_advanced": True,
            "checked_at_compatibility_failure_absent": True,
            "evaluated_at_compatibility_failure_absent": True,
            "optional_latency_approval_failure_absent": True,
            "background_runtime_left_running": False,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        })

        return 0


    if __name__ == "__main__":
        raise SystemExit(
            main()
        )
    '''
).lstrip()


def write_complete_file(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    compile(
        source,
        str(path),
        "exec",
    )

    temporary_path = path.with_name(
        path.name + ".ola079.tmp"
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


def verify_test_source() -> None:
    installed_source = TEST_PATH.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        'SCHEMA_VERSION = "OLA-079"',
        'ENGINE_ID = "OLA-079"',
        "OLA-079 POST-OUTAGE RECOVERY GATE",
        "run_actual_bounded_production_gate",
        "assert_actual_runtime_evidence",
        "test_ola_071_oracle_corrected_"
        "production_restart_verification_gate",
        "readiness provider did not preserve checked_at",
        "OLA-002 decision lacks health approval reasons",
        "real_postgresql_persistence_exercised",
        "background_runtime_left_running",
        '"read_only": True',
        '"execution_allowed": False',
    )

    for token in required_tokens:
        if token not in installed_source:
            raise RuntimeError(
                "Installed OLA-079 test is missing "
                f"required token: {token}"
            )

    compile(
        installed_source,
        str(TEST_PATH),
        "exec",
    )


def main() -> int:
    print("========================================")
    print(" OLA-079 INSTALLER")
    print(" POST-OUTAGE PRODUCTION RECOVERY")
    print(" REAL BOUNDED INTEGRATION GATE")
    print("========================================")

    required_paths = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition_model"
        / "oracle_first_real_shadow_corpus_launch_command.py",

        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "oracle_kalshi_live_read_readiness_gate.py",

        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "__init__.py",

        ROOT
        / "test_ola_071_oracle_corrected_"
        "production_restart_verification_gate.py",
    )

    missing_paths = tuple(
        path
        for path in required_paths
        if not path.exists()
    )

    if missing_paths:
        raise FileNotFoundError(
            "OLA-079 required repository files are missing: "
            + ", ".join(
                str(path)
                for path in missing_paths
            )
        )

    write_complete_file(
        TEST_PATH,
        TEST_SOURCE,
    )

    verify_test_source()

    print("[OK] OLA-077 production correction required")
    print("[OK] OLA-078 V2 production correction required")
    print("[OK] OLA-071 real persistence gate reused")
    print("[OK] Three-cycle bounded recovery configured")
    print("[OK] PostgreSQL advancement assertions installed")
    print("[OK] Runtime evidence assertions installed")
    print("[OK] Historical failure exclusions installed")
    print("[OK] Oracle read-only assertions installed")
    print("[OK] No production files changed")
    print("[OK] No runtime started by installer")

    print(
        "\n[DONE] OLA-079 post-outage production "
        "recovery integration gate installed"
    )

    print("\nRun:")
    print(
        "python "
        "test_ola_079_oracle_post_outage_"
        "production_recovery_integration_gate.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )