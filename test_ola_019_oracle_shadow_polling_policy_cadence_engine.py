from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone


from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessRecord,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_polling_policy_cadence_engine import (
    BLOCKED_STATUS,
    ELIGIBLE_STATUS,
    SUSPENDED_STATUS,
    WAITING_STATUS,
    OracleShadowPollingPolicyCadenceEngine,
    ShadowPollingPolicy,
    ShadowPollingPolicyCompatibilityError,
    ShadowPollingPolicyContractError,
    ShadowPollingState,
)


SOURCE_ID = "source.kalshi.market_data"

ADAPTER_ID = (
    "adapter.oracle.kalshi.public_markets.shadow"
)


READINESS_CHECKED_AT = datetime(
    2026,
    7,
    12,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)

READINESS_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    12,
    0,
    1,
    tzinfo=timezone.utc,
)

FIRST_POLICY_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    12,
    0,
    10,
    tzinfo=timezone.utc,
)

LAST_SUCCESS_AT = datetime(
    2026,
    7,
    12,
    12,
    1,
    0,
    tzinfo=timezone.utc,
)


def build_readiness(
    *,
    evaluated_at=READINESS_EVALUATED_AT,
):
    return KalshiLiveReadReadinessRecord(
        schema_version="OLA-018",
        engine_id="OLA-018",
        readiness_id=(
            "kalshi_live_readiness.test.ola019"
        ),
        readiness_status="passed",
        adapter_id=ADAPTER_ID,
        source_id=SOURCE_ID,
        source_base_url=(
            "https://external-api.kalshi.com/trade-api/v2"
        ),
        source_endpoint="/markets",
        http_method="GET",
        checked_at=READINESS_CHECKED_AT,
        evaluated_at=evaluated_at,
        public_endpoint=True,
        authentication_used=False,
        live_get_request_count=1,
        source_contract_valid=True,
        source_probe_health_status="healthy",
        source_reachable=True,
        source_latency_ms=50,
        source_health_evidence_hash=(
            "a" * 64
        ),
        rate_control_evidence_hash=(
            "b" * 64
        ),
        source_control_decision_hash=(
            "c" * 64
        ),
        source_control_reason_codes=(
            "acquisition_allowed",
            "consecutive_failures_within_policy",
            "latency_within_policy",
            "rate_reserve_preserved",
            "rate_usage_within_limit",
            "source_reachable",
        ),
        health_policy_evidence_present=True,
        rate_policy_evidence_present=True,
        source_control_acquisition_allowed=True,
        shadow_mode=True,
        alerts_allowed=False,
        qseries_intake_allowed=False,
        live_shadow_cycle_entry_ready=True,
        continuous_polling_started=False,
        acquisition_performed=False,
        canonical_observation_created=False,
        persistence_invoked=False,
        alert_created=False,
        qseries_intake_record_created=False,
        reason_codes=(
            "live_shadow_cycle_entry_ready",
        ),
        readiness_metadata=(
            ("environment", "production"),
        ),
        readiness_hash=(
            "d" * 64
        ),
        immutable=True,
        replayable=True,
        auditable=True,
        explainable=True,
        read_only=True,
        execution_allowed=False,
        execution_adapter_resolved=False,
        execution_adapter_invoked=False,
        trade_authorization_allowed=False,
        order_placement_allowed=False,
        funds_moved=False,
        portfolio_mutated=False,
    )


def build_policy():
    return ShadowPollingPolicy.create(
        policy_id="oracle.kalshi.shadow.polling.v1",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        base_interval_seconds=30,
        jitter_max_seconds=5,
        readiness_max_age_seconds=300,
        failure_backoff_base_seconds=30,
        failure_backoff_multiplier=2,
        failure_backoff_max_seconds=600,
        consecutive_failure_suspend_threshold=4,
        suspension_cooldown_seconds=900,
        explicit_restart_evidence_required=True,
        policy_metadata={
            "environment": "production",
            "mode": "shadow",
            "source": "kalshi",
        },
    )


def build_engine():
    return OracleShadowPollingPolicyCadenceEngine(
        policy=build_policy()
    )


def initial_state():
    return ShadowPollingState.create(
        state_id="polling.state.initial",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=None,
        last_cycle_succeeded=None,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "state": "initial",
        },
    )


def successful_state():
    return ShadowPollingState.create(
        state_id="polling.state.success",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=LAST_SUCCESS_AT,
        last_cycle_succeeded=True,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "state": "successful",
        },
    )


def failed_state(
    *,
    failure_count,
    completed_at,
):
    return ShadowPollingState.create(
        state_id=(
            f"polling.state.failure.{failure_count}"
        ),
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=completed_at,
        last_cycle_succeeded=False,
        consecutive_failures=failure_count,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "state": "failed",
            "failure_count": failure_count,
        },
    )


def suspended_state(
    *,
    suspended_at,
    restart_evidence_present,
):
    return ShadowPollingState.create(
        state_id=(
            "polling.state.suspended."
            + (
                "restart"
                if restart_evidence_present
                else "no_restart"
            )
        ),
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=suspended_at,
        last_cycle_succeeded=False,
        consecutive_failures=4,
        suspended=True,
        suspended_at=suspended_at,
        restart_evidence_present=(
            restart_evidence_present
        ),
        state_metadata={
            "state": "suspended",
        },
    )


def evaluate(
    *,
    engine,
    state,
    evaluated_at,
    readiness=None,
):
    return engine.evaluate(
        readiness=(
            build_readiness()
            if readiness is None
            else readiness
        ),
        polling_state=state,
        evaluated_at=evaluated_at,
        decision_metadata={
            "runtime": "future_controlled_scheduler",
            "shadow_mode": True,
        },
    )


def run_policy_contract_test():
    policy = build_policy()

    assert policy.schema_version == "OLA-019"
    assert policy.engine_id == "OLA-019"

    assert policy.policy_id == (
        "oracle.kalshi.shadow.polling.v1"
    )

    assert policy.source_id == SOURCE_ID
    assert policy.adapter_id == ADAPTER_ID

    assert policy.base_interval_seconds == 30
    assert policy.jitter_max_seconds == 5

    assert policy.readiness_max_age_seconds == 300

    assert policy.failure_backoff_base_seconds == 30

    assert policy.failure_backoff_multiplier == 2

    assert policy.failure_backoff_max_seconds == 600

    assert (
        policy.consecutive_failure_suspend_threshold
        == 4
    )

    assert policy.suspension_cooldown_seconds == 900

    assert (
        policy.explicit_restart_evidence_required
        is True
    )

    assert policy.shadow_mode_required is True

    assert policy.alerts_allowed is False

    assert policy.qseries_intake_allowed is False

    assert len(policy.policy_hash) == 64

    assert policy.immutable is True
    assert policy.replayable is True
    assert policy.auditable is True
    assert policy.explainable is True

    assert policy.read_only is True
    assert policy.execution_allowed is False

    assert policy.execution_adapter_resolved is False

    assert policy.execution_adapter_invoked is False

    assert policy.trade_authorization_allowed is False

    assert policy.order_placement_allowed is False

    assert policy.funds_moved is False

    assert policy.portfolio_mutated is False

    try:
        policy.base_interval_seconds = 1

        raise AssertionError(
            "polling policy must be immutable"
        )

    except FrozenInstanceError:
        pass

    return policy


def run_initial_eligibility_test():
    engine = build_engine()

    decision = evaluate(
        engine=engine,
        state=initial_state(),
        evaluated_at=FIRST_POLICY_EVALUATED_AT,
    )

    assert decision.decision_status == ELIGIBLE_STATUS

    assert decision.shadow_cycle_allowed is True

    assert decision.readiness_fresh is True

    assert decision.readiness_age_seconds == 9

    assert decision.base_interval_seconds == 30

    assert (
        0
        <= decision.deterministic_jitter_seconds
        <= 5
    )

    assert decision.failure_backoff_seconds == 0

    assert decision.next_cycle_eligible_at == (
        FIRST_POLICY_EVALUATED_AT
    )

    assert decision.cooldown_elapsed is True

    assert (
        decision.failure_suspend_threshold_reached
        is False
    )

    assert decision.safety_precedence_applied is True

    assert decision.continuous_polling_started is False

    assert decision.acquisition_invoked is False

    assert decision.persistence_invoked is False

    assert decision.alert_created is False

    assert (
        decision.qseries_intake_record_created
        is False
    )

    assert "shadow_cycle_eligible" in decision.reason_codes

    assert decision.read_only is True

    assert decision.execution_allowed is False

    assert decision.execution_adapter_resolved is False

    assert decision.execution_adapter_invoked is False

    assert decision.trade_authorization_allowed is False

    assert decision.order_placement_allowed is False

    assert decision.funds_moved is False

    assert decision.portfolio_mutated is False

    return decision


def run_cadence_waiting_test():
    engine = build_engine()

    state = successful_state()

    baseline = evaluate(
        engine=engine,
        state=state,
        evaluated_at=(
            LAST_SUCCESS_AT
            + timedelta(seconds=1)
        ),
    )

    expected_eligible_at = (
        LAST_SUCCESS_AT
        + timedelta(
            seconds=baseline.effective_interval_seconds
        )
    )

    waiting_at = expected_eligible_at - timedelta(
        seconds=1
    )

    decision = evaluate(
        engine=engine,
        state=state,
        evaluated_at=waiting_at,
    )

    assert decision.decision_status == WAITING_STATUS

    assert decision.shadow_cycle_allowed is False

    assert (
        decision.next_cycle_eligible_at
        == expected_eligible_at
    )

    assert "cadence_interval_active" in decision.reason_codes

    eligible = evaluate(
        engine=engine,
        state=state,
        evaluated_at=expected_eligible_at,
    )

    assert eligible.decision_status == ELIGIBLE_STATUS

    assert eligible.shadow_cycle_allowed is True

    return decision, eligible


def run_failure_backoff_test():
    engine = build_engine()

    completed_at = datetime(
        2026,
        7,
        12,
        12,
        2,
        0,
        tzinfo=timezone.utc,
    )

    expected_backoffs = {
        1: 30,
        2: 60,
        3: 120,
    }

    decisions = {}

    for failure_count, expected_backoff in (
        expected_backoffs.items()
    ):
        state = failed_state(
            failure_count=failure_count,
            completed_at=completed_at,
        )

        probe = evaluate(
            engine=engine,
            state=state,
            evaluated_at=(
                completed_at
                + timedelta(seconds=1)
            ),
        )

        assert (
            probe.failure_backoff_seconds
            == expected_backoff
        )

        eligible_at = probe.next_cycle_eligible_at

        assert eligible_at is not None

        waiting = evaluate(
            engine=engine,
            state=state,
            evaluated_at=(
                eligible_at
                - timedelta(seconds=1)
            ),
        )

        assert waiting.decision_status == WAITING_STATUS

        assert waiting.shadow_cycle_allowed is False

        assert (
            "failure_backoff_active"
            in waiting.reason_codes
        )

        eligible = evaluate(
            engine=engine,
            state=state,
            evaluated_at=eligible_at,
        )

        assert eligible.decision_status == ELIGIBLE_STATUS

        assert eligible.shadow_cycle_allowed is True

        assert (
            "failure_backoff_elapsed"
            in eligible.reason_codes
        )

        decisions[failure_count] = eligible

    return decisions


def run_failure_suspend_threshold_test():
    engine = build_engine()

    state = failed_state(
        failure_count=4,
        completed_at=datetime(
            2026,
            7,
            12,
            12,
            3,
            0,
            tzinfo=timezone.utc,
        ),
    )

    # Deliberately evaluate after readiness is stale.
    #
    # Failure threshold suspension must take precedence and must not be
    # hidden by stale readiness.
    decision = evaluate(
        engine=engine,
        state=state,
        evaluated_at=datetime(
            2026,
            7,
            12,
            12,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert decision.readiness_fresh is False

    assert (
        decision.failure_suspend_threshold_reached
        is True
    )

    assert decision.safety_precedence_applied is True

    assert decision.decision_status == SUSPENDED_STATUS

    assert decision.shadow_cycle_allowed is False

    assert (
        "safety_precedence_failure_threshold"
        in decision.reason_codes
    )

    assert (
        "failure_suspend_threshold_reached"
        in decision.reason_codes
    )

    assert (
        "polling_suspension_required"
        in decision.reason_codes
    )

    return decision


def run_suspension_restart_test():
    engine = build_engine()

    suspended_at = datetime(
        2026,
        7,
        12,
        12,
        5,
        0,
        tzinfo=timezone.utc,
    )

    cooldown_end = suspended_at + timedelta(
        seconds=900
    )

    fresh_restart_readiness = build_readiness(
        evaluated_at=(
            cooldown_end
            - timedelta(seconds=1)
        )
    )

    cooldown_active = evaluate(
        engine=engine,
        state=suspended_state(
            suspended_at=suspended_at,
            restart_evidence_present=False,
        ),
        evaluated_at=(
            cooldown_end
            - timedelta(seconds=1)
        ),
        readiness=fresh_restart_readiness,
    )

    assert (
        cooldown_active.decision_status
        == SUSPENDED_STATUS
    )

    assert cooldown_active.shadow_cycle_allowed is False

    assert cooldown_active.cooldown_elapsed is False

    assert (
        "safety_precedence_existing_suspension"
        in cooldown_active.reason_codes
    )

    assert (
        "suspension_cooldown_active"
        in cooldown_active.reason_codes
    )

    restart_missing = evaluate(
        engine=engine,
        state=suspended_state(
            suspended_at=suspended_at,
            restart_evidence_present=False,
        ),
        evaluated_at=cooldown_end,
        readiness=fresh_restart_readiness,
    )

    assert (
        restart_missing.decision_status
        == SUSPENDED_STATUS
    )

    assert restart_missing.shadow_cycle_allowed is False

    assert restart_missing.cooldown_elapsed is True

    assert (
        "restart_evidence_missing"
        in restart_missing.reason_codes
    )

    stale_restart = evaluate(
        engine=engine,
        state=suspended_state(
            suspended_at=suspended_at,
            restart_evidence_present=True,
        ),
        evaluated_at=cooldown_end,
    )

    assert stale_restart.readiness_fresh is False

    assert stale_restart.decision_status == BLOCKED_STATUS

    assert stale_restart.shadow_cycle_allowed is False

    assert (
        "fresh_readiness_required_after_suspension"
        in stale_restart.reason_codes
    )

    restarted = evaluate(
        engine=engine,
        state=suspended_state(
            suspended_at=suspended_at,
            restart_evidence_present=True,
        ),
        evaluated_at=cooldown_end,
        readiness=fresh_restart_readiness,
    )

    assert restarted.readiness_fresh is True

    assert restarted.decision_status == ELIGIBLE_STATUS

    assert restarted.shadow_cycle_allowed is True

    assert restarted.cooldown_elapsed is True

    assert restarted.restart_evidence_present is True

    assert (
        "restart_evidence_verified"
        in restarted.reason_codes
    )

    return (
        cooldown_active,
        restart_missing,
        stale_restart,
        restarted,
    )


def run_stale_readiness_test():
    engine = build_engine()

    stale_at = (
        READINESS_EVALUATED_AT
        + timedelta(seconds=301)
    )

    decision = evaluate(
        engine=engine,
        state=initial_state(),
        evaluated_at=stale_at,
    )

    assert decision.decision_status == BLOCKED_STATUS

    assert decision.shadow_cycle_allowed is False

    assert decision.readiness_fresh is False

    assert decision.readiness_age_seconds == 301

    assert (
        decision.failure_suspend_threshold_reached
        is False
    )

    assert (
        "safety_precedence_readiness_freshness"
        in decision.reason_codes
    )

    assert "readiness_stale" in decision.reason_codes

    assert (
        "fresh_readiness_required"
        in decision.reason_codes
    )

    return decision


def run_deterministic_replay_test():
    first_engine = build_engine()

    second_engine = build_engine()

    state_one = failed_state(
        failure_count=2,
        completed_at=datetime(
            2026,
            7,
            12,
            12,
            2,
            0,
            tzinfo=timezone.utc,
        ),
    )

    state_two = failed_state(
        failure_count=2,
        completed_at=datetime(
            2026,
            7,
            12,
            12,
            2,
            0,
            tzinfo=timezone.utc,
        ),
    )

    evaluated_at = datetime(
        2026,
        7,
        12,
        12,
        3,
        40,
        tzinfo=timezone.utc,
    )

    first = evaluate(
        engine=first_engine,
        state=state_one,
        evaluated_at=evaluated_at,
    )

    second = evaluate(
        engine=second_engine,
        state=state_two,
        evaluated_at=evaluated_at,
    )

    assert first == second

    assert first.decision_hash == second.decision_hash

    assert (
        first.deterministic_jitter_seconds
        == second.deterministic_jitter_seconds
    )

    assert (
        first.failure_backoff_seconds
        == second.failure_backoff_seconds
    )

    assert (
        first.effective_interval_seconds
        == second.effective_interval_seconds
    )

    assert first.safety_precedence_applied is True

    return first


def run_contract_fail_closed_tests():
    try:
        ShadowPollingPolicy.create(
            policy_id="invalid.multiplier",
            source_id=SOURCE_ID,
            adapter_id=ADAPTER_ID,
            base_interval_seconds=30,
            jitter_max_seconds=5,
            readiness_max_age_seconds=300,
            failure_backoff_base_seconds=30,
            failure_backoff_multiplier=1,
            failure_backoff_max_seconds=600,
            consecutive_failure_suspend_threshold=4,
            suspension_cooldown_seconds=900,
            explicit_restart_evidence_required=True,
            policy_metadata={},
        )

        raise AssertionError(
            "backoff multiplier below 2 must fail closed"
        )

    except ShadowPollingPolicyContractError:
        pass

    try:
        ShadowPollingState.create(
            state_id="invalid.suspended",
            source_id=SOURCE_ID,
            adapter_id=ADAPTER_ID,
            last_cycle_completed_at=LAST_SUCCESS_AT,
            last_cycle_succeeded=False,
            consecutive_failures=4,
            suspended=True,
            suspended_at=None,
            restart_evidence_present=False,
            state_metadata={},
        )

        raise AssertionError(
            "suspended state without suspended_at "
            "must fail closed"
        )

    except ShadowPollingPolicyContractError:
        pass

    engine = build_engine()

    incompatible_readiness = build_readiness()

    object.__setattr__(
        incompatible_readiness,
        "source_control_acquisition_allowed",
        False,
    )

    try:
        engine.evaluate(
            readiness=incompatible_readiness,
            polling_state=initial_state(),
            evaluated_at=FIRST_POLICY_EVALUATED_AT,
            decision_metadata={},
        )

        raise AssertionError(
            "blocked readiness must fail closed"
        )

    except ShadowPollingPolicyCompatibilityError:
        pass

    try:
        engine.evaluate(
            readiness=build_readiness(),
            polling_state=initial_state(),
            evaluated_at=datetime(
                2026,
                7,
                12,
                12,
                0,
                10,
            ),
            decision_metadata={},
        )

        raise AssertionError(
            "naive evaluated_at must fail closed"
        )

    except ShadowPollingPolicyContractError:
        pass

    try:
        engine.evaluate(
            readiness=build_readiness(),
            polling_state=initial_state(),
            evaluated_at=FIRST_POLICY_EVALUATED_AT,
            decision_metadata={
                "api_key": "must-not-enter-evidence",
            },
        )

        raise AssertionError(
            "secret metadata must fail closed"
        )

    except ShadowPollingPolicyContractError:
        pass


def main():
    policy = run_policy_contract_test()

    initial_decision = run_initial_eligibility_test()

    waiting_decision, cadence_eligible = (
        run_cadence_waiting_test()
    )

    backoff_decisions = run_failure_backoff_test()

    suspend_threshold = (
        run_failure_suspend_threshold_test()
    )

    (
        cooldown_active,
        restart_missing,
        stale_restart,
        restarted,
    ) = run_suspension_restart_test()

    stale_decision = run_stale_readiness_test()

    replay_decision = run_deterministic_replay_test()

    run_contract_fail_closed_tests()

    result = {
        "schema_version": policy.schema_version,
        "engine_id": policy.engine_id,
        "status": "passed",
        "policy_id": policy.policy_id,
        "source_id": policy.source_id,
        "adapter_id": policy.adapter_id,
        "base_interval_seconds": (
            policy.base_interval_seconds
        ),
        "jitter_max_seconds": (
            policy.jitter_max_seconds
        ),
        "readiness_max_age_seconds": (
            policy.readiness_max_age_seconds
        ),
        "failure_backoff_base_seconds": (
            policy.failure_backoff_base_seconds
        ),
        "failure_backoff_multiplier": (
            policy.failure_backoff_multiplier
        ),
        "failure_backoff_max_seconds": (
            policy.failure_backoff_max_seconds
        ),
        "consecutive_failure_suspend_threshold": (
            policy.consecutive_failure_suspend_threshold
        ),
        "suspension_cooldown_seconds": (
            policy.suspension_cooldown_seconds
        ),
        "explicit_restart_evidence_required": (
            policy.explicit_restart_evidence_required
        ),
        "safety_precedence_order": (
            "suspension>failure_threshold>"
            "readiness>cadence"
        ),
        "initial_cycle_eligible": (
            initial_decision.shadow_cycle_allowed
        ),
        "cadence_waiting_status": (
            waiting_decision.decision_status
        ),
        "cadence_elapsed_eligible": (
            cadence_eligible.shadow_cycle_allowed
        ),
        "first_failure_backoff_seconds": (
            backoff_decisions[1].failure_backoff_seconds
        ),
        "second_failure_backoff_seconds": (
            backoff_decisions[2].failure_backoff_seconds
        ),
        "third_failure_backoff_seconds": (
            backoff_decisions[3].failure_backoff_seconds
        ),
        "failure_threshold_suspended": (
            suspend_threshold.decision_status
            == SUSPENDED_STATUS
        ),
        "failure_threshold_precedes_stale_readiness": (
            suspend_threshold.readiness_fresh is False
            and suspend_threshold.decision_status
            == SUSPENDED_STATUS
        ),
        "cooldown_active_blocked": (
            cooldown_active.shadow_cycle_allowed
            is False
        ),
        "restart_evidence_missing_blocked": (
            restart_missing.shadow_cycle_allowed
            is False
        ),
        "stale_restart_readiness_blocked": (
            stale_restart.decision_status
            == BLOCKED_STATUS
        ),
        "fresh_restart_readiness_required": True,
        "restart_evidence_restores_eligibility": (
            restarted.shadow_cycle_allowed
        ),
        "stale_readiness_blocked": (
            stale_decision.decision_status
            == BLOCKED_STATUS
        ),
        "deterministic_jitter": True,
        "deterministic_backoff": True,
        "deterministic_replay_valid": (
            replay_decision.read_only
        ),
        "safety_precedence_applied": (
            initial_decision.safety_precedence_applied
        ),
        "continuous_polling_started": (
            initial_decision.continuous_polling_started
        ),
        "acquisition_invoked": (
            initial_decision.acquisition_invoked
        ),
        "persistence_invoked": (
            initial_decision.persistence_invoked
        ),
        "alert_created": (
            initial_decision.alert_created
        ),
        "qseries_intake_record_created": (
            initial_decision
            .qseries_intake_record_created
        ),
        "shadow_mode_required": (
            policy.shadow_mode_required
        ),
        "alerts_allowed": policy.alerts_allowed,
        "qseries_intake_allowed": (
            policy.qseries_intake_allowed
        ),
        "read_only": initial_decision.read_only,
        "execution_allowed": (
            initial_decision.execution_allowed
        ),
        "execution_adapter_resolved": (
            initial_decision.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            initial_decision.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            initial_decision.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            initial_decision.order_placement_allowed
        ),
        "funds_moved": initial_decision.funds_moved,
        "portfolio_mutated": (
            initial_decision.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-019 Oracle Shadow Polling Policy "
        "and Cadence Engine"
    )

    print(result)


if __name__ == "__main__":
    main()
