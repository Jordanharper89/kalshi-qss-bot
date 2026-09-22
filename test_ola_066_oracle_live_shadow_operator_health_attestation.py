from __future__ import annotations

from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_attestation import (
    OracleLiveShadowOperatorHealthAttestationBlocked,
    OracleLiveShadowOperatorHealthAttestor,
)


OBSERVED_AT = datetime(
    2026,
    7,
    17,
    20,
    0,
    0,
    tzinfo=timezone.utc,
)


def expect_blocked(callable_object) -> None:
    try:
        callable_object()
    except OracleLiveShadowOperatorHealthAttestationBlocked:
        return

    raise AssertionError(
        "expected OLA-066 to fail closed"
    )


def main() -> int:
    def healthy_provider(*, stale_seconds):
        assert stale_seconds == 120

        return {
            "status": "RUNNING",
            "pid": 12345,
            "process_alive": True,
            "runtime_fresh": True,
            "state_age_seconds": 3.0,
            "newest_log_age_seconds": 2.0,
            "read_only": True,
            "execution_allowed": False,
        }

    attestor = OracleLiveShadowOperatorHealthAttestor(
        status_provider=healthy_provider
    )

    first = attestor.attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )

    second = attestor.attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )

    assert first == second
    assert first.operator_status == "RUNNING"
    assert first.health_status == "HEALTHY"
    assert first.healthy is True
    assert first.degraded is False
    assert first.stopped is False
    assert first.fail_closed is False
    assert first.read_only is True
    assert first.execution_allowed is False
    assert first.alerts_allowed is False
    assert first.qseries_handoff_allowed is False
    assert first.execution_adapter_resolved is False
    assert first.execution_adapter_invoked is False
    assert first.trade_authorization_allowed is False
    assert first.order_placement_allowed is False
    assert first.funds_moved is False
    assert first.portfolio_mutated is False
    assert first.evidence_hash == second.evidence_hash

    immutable_payload = first.to_dict()

    try:
        immutable_payload["healthy"] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "health projection must be immutable"
        )

    degraded = OracleLiveShadowOperatorHealthAttestor(
        status_provider=lambda **_: {
            "status": "DEGRADED",
            "pid": 12346,
            "process_alive": True,
            "runtime_fresh": False,
            "state_age_seconds": 150.0,
            "newest_log_age_seconds": 151.0,
            "read_only": True,
            "execution_allowed": False,
        }
    ).attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )

    assert degraded.degraded is True
    assert degraded.fail_closed is True

    stopped = OracleLiveShadowOperatorHealthAttestor(
        status_provider=lambda **_: {
            "status": "STOPPED",
            "pid": None,
            "process_alive": False,
            "runtime_fresh": False,
            "state_age_seconds": None,
            "newest_log_age_seconds": None,
            "read_only": True,
            "execution_allowed": False,
        }
    ).attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )

    assert stopped.stopped is True
    assert stopped.fail_closed is True

    expect_blocked(
        lambda: attestor.attest(
            observed_at=datetime(
                2026,
                7,
                17,
                20,
                0,
                0,
            )
        )
    )

    expect_blocked(
        lambda: OracleLiveShadowOperatorHealthAttestor(
            status_provider=lambda **_: {
                "status": "RUNNING",
                "pid": 12345,
                "process_alive": True,
                "runtime_fresh": True,
                "state_age_seconds": 1.0,
                "newest_log_age_seconds": 1.0,
                "read_only": False,
                "execution_allowed": False,
            }
        ).attest(
            observed_at=OBSERVED_AT
        )
    )

    expect_blocked(
        lambda: OracleLiveShadowOperatorHealthAttestor(
            status_provider=lambda **_: {
                "status": "RUNNING",
                "pid": 12345,
                "process_alive": True,
                "runtime_fresh": True,
                "state_age_seconds": 1.0,
                "newest_log_age_seconds": 1.0,
                "read_only": True,
                "execution_allowed": True,
            }
        ).attest(
            observed_at=OBSERVED_AT
        )
    )

    expect_blocked(
        lambda: OracleLiveShadowOperatorHealthAttestor(
            status_provider=lambda **_: {
                "status": "RUNNING",
                "pid": None,
                "process_alive": True,
                "runtime_fresh": True,
                "state_age_seconds": 1.0,
                "newest_log_age_seconds": 1.0,
                "read_only": True,
                "execution_allowed": False,
            }
        ).attest(
            observed_at=OBSERVED_AT
        )
    )

    print(
        "[PASS] OLA-066 Oracle Live Shadow "
        "Operator Health Attestation"
    )

    print(
        {
            "schema_version": "OLA-066",
            "engine_id": "OLA-066",
            "status": "passed",
            "ola064_status_provider_consumed": True,
            "invalid_brittle_marker_checks_removed": True,
            "healthy_attestation": True,
            "degraded_fail_closed": True,
            "stopped_fail_closed": True,
            "deterministic_evidence_hash": True,
            "immutable_record": True,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
