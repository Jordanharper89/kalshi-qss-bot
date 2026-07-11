
from dataclasses import (
    FrozenInstanceError,
    dataclass,
)
import json
from pathlib import Path

from qseries_v2.integration.qseries_final_execution_authorization_gate import (
    ADAPTER_EXECUTION_REQUIRED,
    ENGINE_ID,
    EXECUTION_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    FinalExecutionAuthorizationStatus,
    QSeriesFinalExecutionAuthorizationResult,
    authorize_execution_readiness,
    validate_qseries_final_execution_authorization_result,
)


AUTHORIZED_AT = (
    "2026-07-11T00:00:00+00:00"
)


@dataclass(frozen=True)
class FakeReadyRecord:
    readiness_id: str
    opportunity_id: str
    status: str = (
        "ready_for_execution_gate"
    )
    record_hash: str = (
        "record_hash_001"
    )
    qseries_owned: bool = True
    execution_allowed: bool = False
    final_execution_gate_required: (
        bool
    ) = True

    def as_dict(
        self,
    ):
        return {
            "readiness_id": (
                self.readiness_id
            ),
            "opportunity_id": (
                self.opportunity_id
            ),
            "status": self.status,
            "record_hash": (
                self.record_hash
            ),
            "qseries_owned": (
                self.qseries_owned
            ),
            "execution_allowed": (
                self.execution_allowed
            ),
            "final_execution_gate_required": (
                self.final_execution_gate_required
            ),
        }


@dataclass(frozen=True)
class FakeReadinessResult:
    schema_version: str = "INT-014"
    engine_id: str = "INT-014"
    status: str = "passed"
    ready_records: tuple = (
        FakeReadyRecord(
            "int014_ready_001",
            "opp_001",
        ),
        FakeReadyRecord(
            "int014_ready_002",
            "opp_002",
            record_hash=(
                "record_hash_002"
            ),
        ),
    )
    ready_count: int = 2
    rejected_count: int = 0
    result_hash: str = (
        "int014_result_hash"
    )
    read_only: bool = True
    execution_allowed: bool = False
    final_execution_gate_required: (
        bool
    ) = True
    qseries_owned: bool = True

    def as_dict(
        self,
    ):
        return {
            "schema_version": (
                self.schema_version
            ),
            "engine_id": (
                self.engine_id
            ),
            "status": self.status,
            "ready_records": [
                record.as_dict()
                for record
                in self.ready_records
            ],
            "ready_count": (
                self.ready_count
            ),
            "rejected_count": (
                self.rejected_count
            ),
            "result_hash": (
                self.result_hash
            ),
            "read_only": (
                self.read_only
            ),
            "execution_allowed": (
                self.execution_allowed
            ),
            "final_execution_gate_required": (
                self.final_execution_gate_required
            ),
            "qseries_owned": (
                self.qseries_owned
            ),
        }


def test_valid_result():
    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    assert (
        result.schema_version
        == SCHEMA_VERSION
    )

    assert (
        result.engine_id
        == ENGINE_ID
    )

    assert result.status == "passed"

    assert (
        result.authorized_count
        == 2
    )

    assert result.blocked_count == 0

    assert all(
        decision.status
        is FinalExecutionAuthorizationStatus.AUTHORIZED
        for decision in result.decisions
    )

    assert (
        validate_qseries_final_execution_authorization_result(
            result
        )
    )


def test_failed_readiness_result():
    result = authorize_execution_readiness(
        FakeReadinessResult(
            status="failed",
            ready_records=tuple(),
            ready_count=0,
            rejected_count=1,
        ),
        authorized_at=AUTHORIZED_AT,
    )

    assert result.status == "failed"

    assert (
        result.authorized_count
        == 0
    )

    assert result.rejection_reasons


def test_malformed_contract():
    result = authorize_execution_readiness(
        FakeReadinessResult(
            schema_version="INT-999"
        ),
        authorized_at=AUTHORIZED_AT,
    )

    assert result.status == "failed"

    assert (
        "source_contract"
        in result.rejection_reasons
    )


def test_invalid_record_blocked():
    invalid_record = FakeReadyRecord(
        readiness_id="int014_bad",
        opportunity_id="opp_bad",
        status="blocked",
    )

    result = authorize_execution_readiness(
        FakeReadinessResult(
            ready_records=(
                invalid_record,
            ),
            ready_count=1,
        ),
        authorized_at=AUTHORIZED_AT,
    )

    assert result.status == "failed"

    assert result.blocked_count == 1


def test_deterministic_result():
    first = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    second = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    assert first == second

    assert (
        first.result_hash
        == second.result_hash
    )


def test_timestamp_identity():
    first = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=(
            "2026-07-11T00:00:00+00:00"
        ),
    )

    second = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=(
            "2026-07-11T00:01:00+00:00"
        ),
    )

    assert (
        first.result_hash
        != second.result_hash
    )

    assert [
        decision.authorization_id
        for decision in first.decisions
    ] == [
        decision.authorization_id
        for decision in second.decisions
    ]

    assert [
        decision.semantic_hash
        for decision in first.decisions
    ] == [
        decision.semantic_hash
        for decision in second.decisions
    ]


def test_result_frozen():
    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    try:
        result.status = "failed"
        raise AssertionError(
            "result was mutable"
        )
    except FrozenInstanceError:
        pass


def test_json_serialization():
    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    encoded = json.dumps(
        result.as_dict(),
        sort_keys=True,
    )

    decoded = json.loads(
        encoded
    )

    assert (
        decoded["schema_version"]
        == "INT-015"
    )

    assert (
        decoded["authorized_count"]
        == 2
    )


def test_no_side_effects():
    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    telemetry = dict(
        result.telemetry
    )

    assert (
        telemetry["orders_placed"]
        is False
    )

    assert (
        telemetry["exchange_called"]
        is False
    )

    assert (
        telemetry["funds_moved"]
        is False
    )

    assert (
        telemetry["portfolio_mutated"]
        is False
    )

    assert (
        telemetry["files_written"]
        is False
    )

    assert (
        telemetry["database_written"]
        is False
    )

    assert (
        result.read_only
        is READ_ONLY
        is True
    )

    assert (
        result.execution_allowed
        is EXECUTION_ALLOWED
        is False
    )

    assert (
        result.adapter_execution_required
        is ADAPTER_EXECUTION_REQUIRED
        is True
    )


def test_package_export():
    from qseries_v2.integration import (
        QSeriesFinalExecutionAuthorizationResult
        as ExportedResult,
    )

    from qseries_v2.integration import (
        authorize_execution_readiness
        as exported_authorize,
    )

    assert (
        ExportedResult
        is QSeriesFinalExecutionAuthorizationResult
    )

    assert (
        exported_authorize
        is authorize_execution_readiness
    )


def test_installer_idempotence():
    root = Path(
        __file__
    ).resolve().parent

    module_path = (
        root
        / "qseries_v2"
        / "integration"
        / "qseries_final_execution_authorization_gate.py"
    )

    test_path = (
        root
        / "test_int_015_qseries_final_execution_authorization_gate.py"
    )

    init_path = (
        root
        / "qseries_v2"
        / "integration"
        / "__init__.py"
    )

    before = (
        module_path.read_bytes(),
        test_path.read_bytes(),
        init_path.read_bytes(),
    )

    installer_path = (
        root
        / "build_int_015_qseries_final_execution_authorization_gate.py"
    )

    namespace = {
        "__name__": (
            "__installer_test__"
        )
    }

    exec(
        compile(
            installer_path.read_text(
                encoding="utf-8"
            ),
            str(
                installer_path
            ),
            "exec",
        ),
        namespace,
    )

    after = (
        module_path.read_bytes(),
        test_path.read_bytes(),
        init_path.read_bytes(),
    )

    assert before == after


def run_all():
    tests = (
        test_valid_result,
        test_failed_readiness_result,
        test_malformed_contract,
        test_invalid_record_blocked,
        test_deterministic_result,
        test_timestamp_identity,
        test_result_frozen,
        test_json_serialization,
        test_no_side_effects,
        test_package_export,
        test_installer_idempotence,
    )

    for test in tests:
        test()

    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    print(
        "[PASS] INT-015 "
        "Q Series Final Execution "
        "Authorization Gate"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": (
                result.engine_id
            ),
            "status": (
                result.status
            ),
            "authorized_count": (
                result.authorized_count
            ),
            "blocked_count": (
                result.blocked_count
            ),
            "read_only": (
                result.read_only
            ),
            "execution_allowed": (
                result.execution_allowed
            ),
            "adapter_execution_required": (
                result.adapter_execution_required
            ),
        }
    )


if __name__ == "__main__":
    run_all()
