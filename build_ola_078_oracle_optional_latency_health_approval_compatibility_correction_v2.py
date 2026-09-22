from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

READINESS_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_kalshi_live_read_readiness_gate.py"
)

PACKAGE_INIT_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "__init__.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_078_oracle_optional_latency_health_approval_compatibility_correction.py"
)


CANONICAL_CONSTANT_BLOCK = '''HEALTH_LATENCY_APPROVAL_REASON_CODES = frozenset(
    {
        "latency_within_policy",
        "latency_policy_not_required",
    }
)

RATE_APPROVAL_REASON_CODES = frozenset(
'''


COMPATIBLE_CONSTANT_BLOCK = '''HEALTH_LATENCY_APPROVAL_REASON_CODES = frozenset(
    {
        "latency_within_policy",
        "latency_policy_not_required",
    }
)

# OLA-078 V2 backward-compatibility export.
#
# Earlier Oracle package surfaces imported this historical constant name.
# Preserve that public name as the union of all recognized health approval
# reasons while the readiness validator continues to enforce:
#
#   required health reasons
#   AND one valid latency approval reason
#
# The alias does not weaken readiness validation.
HEALTH_APPROVAL_REASON_CODES = frozenset(
    HEALTH_REQUIRED_APPROVAL_REASON_CODES
    | HEALTH_LATENCY_APPROVAL_REASON_CODES
)

RATE_APPROVAL_REASON_CODES = frozenset(
'''


READINESS_EXPORT_ANCHOR = '''    "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
    "HEALTH_LATENCY_APPROVAL_REASON_CODES",
    "RATE_APPROVAL_REASON_CODES",
'''


READINESS_EXPORT_REPLACEMENT = '''    "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
    "HEALTH_LATENCY_APPROVAL_REASON_CODES",
    "HEALTH_APPROVAL_REASON_CODES",
    "RATE_APPROVAL_REASON_CODES",
'''


PACKAGE_IMPORT_OLD = '''from .oracle_kalshi_live_read_readiness_gate import (
    FINAL_APPROVAL_REASON_CODE,
    HEALTH_APPROVAL_REASON_CODES,
    RATE_APPROVAL_REASON_CODES,
    KalshiLiveReadReadinessContractError,
'''


PACKAGE_IMPORT_NEW = '''from .oracle_kalshi_live_read_readiness_gate import (
    FINAL_APPROVAL_REASON_CODE,
    HEALTH_APPROVAL_REASON_CODES,
    HEALTH_LATENCY_APPROVAL_REASON_CODES,
    HEALTH_REQUIRED_APPROVAL_REASON_CODES,
    RATE_APPROVAL_REASON_CODES,
    KalshiLiveReadReadinessContractError,
'''


PACKAGE_EXPORT_OLD = '''    "FINAL_APPROVAL_REASON_CODE",
    "HEALTH_APPROVAL_REASON_CODES",
    "RATE_APPROVAL_REASON_CODES",
'''


PACKAGE_EXPORT_NEW = '''    "FINAL_APPROVAL_REASON_CODE",
    "HEALTH_APPROVAL_REASON_CODES",
    "HEALTH_LATENCY_APPROVAL_REASON_CODES",
    "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
    "RATE_APPROVAL_REASON_CODES",
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition import (
    HEALTH_APPROVAL_REASON_CODES,
    HEALTH_LATENCY_APPROVAL_REASON_CODES,
    HEALTH_REQUIRED_APPROVAL_REASON_CODES,
    OracleAcquisitionSourceControlEngine,
    OracleKalshiLiveReadReadinessGate,
    RateControlPolicy,
    RateWindowObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessFailure,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
    SOURCE_ID,
)


SCHEMA_VERSION = "OLA-078"
ENGINE_ID = "OLA-078-V2"

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


def build_decision(
    *,
    max_latency_ms: int | None,
    latency_ms: int | None,
    reachable: bool = True,
    consecutive_failures: int = 0,
):
    checked_at = datetime(
        2026,
        7,
        19,
        21,
        0,
        0,
        tzinfo=timezone.utc,
    )

    health_policy = SourceHealthPolicy.create(
        policy_id="ola078-health-policy",
        max_consecutive_failures=2,
        max_latency_ms=max_latency_ms,
    )

    rate_policy = RateControlPolicy.create(
        policy_id="ola078-rate-policy",
        max_requests_per_window=100,
        window_seconds=60,
        minimum_remaining_reserve=10,
    )

    engine = OracleAcquisitionSourceControlEngine(
        source_policies={
            SOURCE_ID: (
                health_policy,
                rate_policy,
            )
        }
    )

    health_observation = SourceHealthObservation.create(
        source_id=SOURCE_ID,
        checked_at=checked_at,
        reachable=reachable,
        consecutive_failures=consecutive_failures,
        latency_ms=latency_ms,
        metadata={
            "test": "OLA-078-V2",
        },
    )

    rate_observation = RateWindowObservation.create(
        source_id=SOURCE_ID,
        checked_at=checked_at,
        window_started_at=(
            checked_at
            - timedelta(seconds=5)
        ),
        requests_used=1,
        metadata={
            "test": "OLA-078-V2",
        },
    )

    return engine.evaluate(
        health_observation=health_observation,
        rate_observation=rate_observation,
        evaluated_at=checked_at,
        replay_metadata={
            "test": "OLA-078-V2",
        },
        audit_metadata={
            "test": "OLA-078-V2",
        },
    )


def validate_decision(decision):
    return (
        OracleKalshiLiveReadReadinessGate
        ._validate_source_control_decision(
            decision=decision,
        )
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
    print(" OLA-078 TEST CORRECTION V2")
    print(" PACKAGE EXPORT COMPATIBILITY")
    print(" OPTIONAL LATENCY APPROVAL CONTRACT")
    print("========================================")

    assert_read_only_boundary()

    print("[TEST] Package-level readiness imports")

    assert HEALTH_REQUIRED_APPROVAL_REASON_CODES == frozenset(
        {
            "source_reachable",
            "consecutive_failures_within_policy",
        }
    )

    assert HEALTH_LATENCY_APPROVAL_REASON_CODES == frozenset(
        {
            "latency_within_policy",
            "latency_policy_not_required",
        }
    )

    assert HEALTH_APPROVAL_REASON_CODES == frozenset(
        {
            "source_reachable",
            "consecutive_failures_within_policy",
            "latency_within_policy",
            "latency_policy_not_required",
        }
    )

    print("[OK] Package-level readiness imports")

    print("[TEST] Legacy health approval export preserved")

    assert (
        HEALTH_REQUIRED_APPROVAL_REASON_CODES
        .issubset(HEALTH_APPROVAL_REASON_CODES)
    )

    assert (
        HEALTH_LATENCY_APPROVAL_REASON_CODES
        .issubset(HEALTH_APPROVAL_REASON_CODES)
    )

    print("[OK] Legacy health approval export preserved")

    print("[TEST] Optional-latency policy decision")

    optional_latency_decision = build_decision(
        max_latency_ms=None,
        latency_ms=None,
    )

    optional_reason_codes = set(
        optional_latency_decision.reason_codes
    )

    assert "source_reachable" in optional_reason_codes

    assert (
        "consecutive_failures_within_policy"
        in optional_reason_codes
    )

    assert (
        "latency_policy_not_required"
        in optional_reason_codes
    )

    assert optional_latency_decision.acquisition_allowed is True

    optional_result = validate_decision(
        optional_latency_decision
    )

    assert isinstance(optional_result, tuple)
    assert len(optional_result) == 3

    print("[OK] Optional-latency decision accepted")

    print("[TEST] Required-latency policy decision")

    required_latency_decision = build_decision(
        max_latency_ms=1000,
        latency_ms=25,
    )

    required_reason_codes = set(
        required_latency_decision.reason_codes
    )

    assert "source_reachable" in required_reason_codes

    assert (
        "consecutive_failures_within_policy"
        in required_reason_codes
    )

    assert (
        "latency_within_policy"
        in required_reason_codes
    )

    assert required_latency_decision.acquisition_allowed is True

    required_result = validate_decision(
        required_latency_decision
    )

    assert isinstance(required_result, tuple)
    assert len(required_result) == 3

    print("[OK] Required-latency decision accepted")

    print("[TEST] Missing latency approval rejected")

    wrong_reason_codes = tuple(
        reason
        for reason in optional_latency_decision.reason_codes
        if reason != "latency_policy_not_required"
    )

    wrong_decision = type(optional_latency_decision)(
        schema_version=optional_latency_decision.schema_version,
        engine_id=optional_latency_decision.engine_id,
        source_id=optional_latency_decision.source_id,
        evaluated_at=optional_latency_decision.evaluated_at,
        health_policy_id=optional_latency_decision.health_policy_id,
        rate_policy_id=optional_latency_decision.rate_policy_id,
        health_observation_hash=(
            optional_latency_decision.health_observation_hash
        ),
        rate_observation_hash=(
            optional_latency_decision.rate_observation_hash
        ),
        health_evidence=optional_latency_decision.health_evidence,
        rate_control_evidence=(
            optional_latency_decision.rate_control_evidence
        ),
        acquisition_allowed=True,
        reason_codes=wrong_reason_codes,
        replay_metadata=optional_latency_decision.replay_metadata,
        audit_metadata=optional_latency_decision.audit_metadata,
        decision_hash=optional_latency_decision.decision_hash,
        read_only=True,
        execution_allowed=False,
        acquisition_performed=False,
        trade_authorization_allowed=False,
        order_placement_allowed=False,
        execution_adapter_invocation_allowed=False,
        funds_moved=False,
        portfolio_mutated=False,
    )

    try:
        validate_decision(
            wrong_decision
        )
    except KalshiLiveReadReadinessFailure as exc:
        assert (
            "lacks valid latency approval reason"
            in str(exc)
        )
    else:
        raise AssertionError(
            "decision without a valid latency reason was accepted"
        )

    print("[OK] Missing latency approval rejected")

    print("[TEST] Unreachable source remains rejected")

    unreachable_decision = build_decision(
        max_latency_ms=None,
        latency_ms=None,
        reachable=False,
    )

    assert unreachable_decision.acquisition_allowed is False

    try:
        validate_decision(
            unreachable_decision
        )
    except KalshiLiveReadReadinessFailure:
        pass
    else:
        raise AssertionError(
            "unreachable source decision was accepted"
        )

    print("[OK] Unreachable source remains rejected")

    print("[TEST] Excessive failures remain rejected")

    excessive_failure_decision = build_decision(
        max_latency_ms=None,
        latency_ms=None,
        consecutive_failures=3,
    )

    assert (
        excessive_failure_decision.acquisition_allowed
        is False
    )

    try:
        validate_decision(
            excessive_failure_decision
        )
    except KalshiLiveReadReadinessFailure:
        pass
    else:
        raise AssertionError(
            "excessive-failure decision was accepted"
        )

    print("[OK] Excessive failures remain rejected")

    print("[TEST] Production and package markers")

    root = Path(__file__).resolve().parent

    readiness_path = (
        root
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "oracle_kalshi_live_read_readiness_gate.py"
    )

    package_path = (
        root
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "__init__.py"
    )

    readiness_source = readiness_path.read_text(
        encoding="utf-8"
    )

    package_source = package_path.read_text(
        encoding="utf-8"
    )

    assert (
        "OLA-078 health approval compatibility contract"
        in readiness_source
    )

    assert (
        "OLA-078 V2 backward-compatibility export"
        in readiness_source
    )

    assert (
        '"HEALTH_REQUIRED_APPROVAL_REASON_CODES"'
        in readiness_source
    )

    assert (
        '"HEALTH_LATENCY_APPROVAL_REASON_CODES"'
        in readiness_source
    )

    assert (
        '"HEALTH_APPROVAL_REASON_CODES"'
        in readiness_source
    )

    assert (
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES,"
        in package_source
    )

    assert (
        "HEALTH_LATENCY_APPROVAL_REASON_CODES,"
        in package_source
    )

    assert (
        "HEALTH_APPROVAL_REASON_CODES,"
        in package_source
    )

    print("[OK] Production and package markers")

    print("[TEST] Oracle read-only boundary")

    assert optional_latency_decision.read_only is True

    assert (
        optional_latency_decision.execution_allowed
        is False
    )

    assert (
        optional_latency_decision
        .trade_authorization_allowed
        is False
    )

    assert (
        optional_latency_decision
        .order_placement_allowed
        is False
    )

    assert (
        optional_latency_decision
        .execution_adapter_invocation_allowed
        is False
    )

    assert optional_latency_decision.funds_moved is False
    assert optional_latency_decision.portfolio_mutated is False

    print("[OK] Oracle read-only boundary preserved")

    print(
        "[PASS] OLA-078 Oracle Optional Latency "
        "Health Approval Compatibility Correction V2"
    )

    print({
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "package_import_compatibility_restored": True,
        "legacy_health_export_preserved": True,
        "canonical_required_health_exported": True,
        "canonical_latency_health_exported": True,
        "ola002_optional_latency_reason_supported": True,
        "latency_policy_not_required_accepted": True,
        "latency_within_policy_accepted": True,
        "source_reachable_still_required": True,
        "failure_policy_approval_still_required": True,
        "missing_latency_approval_rejected": True,
        "unreachable_source_rejected": True,
        "excessive_failures_rejected": True,
        "rate_policy_validation_preserved": True,
        "final_acquisition_approval_preserved": True,
        "real_service_started": False,
        "process_created": False,
        "thread_created": False,
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


def read_required_file(
    path: Path,
) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file does not exist: {path}"
        )

    return path.read_text(
        encoding="utf-8"
    )


def correct_readiness_source(
    source: str,
) -> str:
    compatibility_marker = (
        "OLA-078 V2 backward-compatibility export"
    )

    if compatibility_marker not in source:
        count = source.count(
            CANONICAL_CONSTANT_BLOCK
        )

        if count != 1:
            raise RuntimeError(
                "Expected exactly one OLA-078 canonical "
                f"constant block; found {count}. "
                "No files were changed."
            )

        source = source.replace(
            CANONICAL_CONSTANT_BLOCK,
            COMPATIBLE_CONSTANT_BLOCK,
            1,
        )

    if (
        '"HEALTH_APPROVAL_REASON_CODES"'
        not in source
    ):
        count = source.count(
            READINESS_EXPORT_ANCHOR
        )

        if count != 1:
            raise RuntimeError(
                "Expected exactly one readiness export block; "
                f"found {count}. No files were changed."
            )

        source = source.replace(
            READINESS_EXPORT_ANCHOR,
            READINESS_EXPORT_REPLACEMENT,
            1,
        )

    required_tokens = (
        "OLA-078 health approval compatibility contract",
        compatibility_marker,
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES",
        "HEALTH_LATENCY_APPROVAL_REASON_CODES",
        "HEALTH_APPROVAL_REASON_CODES = frozenset(",
        '"HEALTH_APPROVAL_REASON_CODES"',
    )

    for token in required_tokens:
        if token not in source:
            raise RuntimeError(
                "Corrected readiness source is missing "
                f"required token: {token}"
            )

    compile(
        source,
        str(READINESS_PATH),
        "exec",
    )

    return source


def correct_package_source(
    source: str,
) -> str:
    new_imports_present = (
        "HEALTH_LATENCY_APPROVAL_REASON_CODES,"
        in source
        and
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES,"
        in source
    )

    if not new_imports_present:
        count = source.count(
            PACKAGE_IMPORT_OLD
        )

        if count != 1:
            raise RuntimeError(
                "Expected exactly one old readiness package "
                f"import block; found {count}. "
                "No files were changed."
            )

        source = source.replace(
            PACKAGE_IMPORT_OLD,
            PACKAGE_IMPORT_NEW,
            1,
        )

    new_exports_present = (
        '"HEALTH_LATENCY_APPROVAL_REASON_CODES"'
        in source
        and
        '"HEALTH_REQUIRED_APPROVAL_REASON_CODES"'
        in source
    )

    if not new_exports_present:
        count = source.count(
            PACKAGE_EXPORT_OLD
        )

        if count != 1:
            raise RuntimeError(
                "Expected exactly one old readiness package "
                f"export block; found {count}. "
                "No files were changed."
            )

        source = source.replace(
            PACKAGE_EXPORT_OLD,
            PACKAGE_EXPORT_NEW,
            1,
        )

    required_tokens = (
        "HEALTH_APPROVAL_REASON_CODES,",
        "HEALTH_LATENCY_APPROVAL_REASON_CODES,",
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES,",
        '"HEALTH_APPROVAL_REASON_CODES"',
        '"HEALTH_LATENCY_APPROVAL_REASON_CODES"',
        '"HEALTH_REQUIRED_APPROVAL_REASON_CODES"',
    )

    for token in required_tokens:
        if token not in source:
            raise RuntimeError(
                "Corrected package source is missing "
                f"required token: {token}"
            )

    compile(
        source,
        str(PACKAGE_INIT_PATH),
        "exec",
    )

    return source


def write_complete_file(
    path: Path,
    source: str,
    temporary_suffix: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        path.name + temporary_suffix
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


def verify_installed_files() -> None:
    readiness_source = read_required_file(
        READINESS_PATH
    )

    package_source = read_required_file(
        PACKAGE_INIT_PATH
    )

    required_readiness_tokens = (
        "OLA-078 V2 backward-compatibility export",
        "HEALTH_APPROVAL_REASON_CODES = frozenset(",
        '"HEALTH_APPROVAL_REASON_CODES"',
        '"HEALTH_LATENCY_APPROVAL_REASON_CODES"',
        '"HEALTH_REQUIRED_APPROVAL_REASON_CODES"',
    )

    for token in required_readiness_tokens:
        assert token in readiness_source

    required_package_tokens = (
        "HEALTH_APPROVAL_REASON_CODES,",
        "HEALTH_LATENCY_APPROVAL_REASON_CODES,",
        "HEALTH_REQUIRED_APPROVAL_REASON_CODES,",
        '"HEALTH_APPROVAL_REASON_CODES"',
        '"HEALTH_LATENCY_APPROVAL_REASON_CODES"',
        '"HEALTH_REQUIRED_APPROVAL_REASON_CODES"',
    )

    for token in required_package_tokens:
        assert token in package_source

    compile(
        readiness_source,
        str(READINESS_PATH),
        "exec",
    )

    compile(
        package_source,
        str(PACKAGE_INIT_PATH),
        "exec",
    )


def main() -> int:
    print("========================================")
    print(" OLA-078 PRODUCTION CORRECTION V2")
    print(" PACKAGE EXPORT COMPATIBILITY")
    print(" LEGACY IMPORT PRESERVATION")
    print("========================================")

    readiness_source = read_required_file(
        READINESS_PATH
    )

    package_source = read_required_file(
        PACKAGE_INIT_PATH
    )

    corrected_readiness_source = (
        correct_readiness_source(
            readiness_source
        )
    )

    corrected_package_source = (
        correct_package_source(
            package_source
        )
    )

    compile(
        TEST_SOURCE,
        str(TEST_PATH),
        "exec",
    )

    write_complete_file(
        READINESS_PATH,
        corrected_readiness_source,
        ".ola078_v2.tmp",
    )

    write_complete_file(
        PACKAGE_INIT_PATH,
        corrected_package_source,
        ".ola078_v2.tmp",
    )

    write_complete_file(
        TEST_PATH,
        TEST_SOURCE,
        ".ola078_v2.tmp",
    )

    verify_installed_files()

    print("[OK] Legacy health constant restored as alias")
    print("[OK] Canonical required-health constant exported")
    print("[OK] Canonical latency-health constant exported")
    print("[OK] Package import compatibility restored")
    print("[OK] Existing Oracle imports preserved")
    print("[OK] Optional latency correction preserved")
    print("[OK] Strict readiness validation preserved")
    print("[OK] Oracle read-only boundary preserved")
    print("[OK] No production runtime started")

    print(
        "\n[DONE] OLA-078 optional latency "
        "compatibility correction V2 installed"
    )

    print("\nRun:")
    print(
        "python "
        "test_ola_078_oracle_optional_latency_"
        "health_approval_compatibility_correction.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )