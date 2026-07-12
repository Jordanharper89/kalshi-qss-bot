from dataclasses import FrozenInstanceError
from datetime import datetime, timezone


from qseries_v2.oracle_intelligence.live_acquisition import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceHealthPolicy,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
    PRODUCTION_BASE_URL,
    OracleKalshiPublicMarketShadowSourceAdapter,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessContractError,
    KalshiLiveReadReadinessFailure,
    OracleKalshiLiveReadReadinessGate,
)


CHECKED_AT = datetime(
    2026,
    7,
    12,
    11,
    0,
    0,
    tzinfo=timezone.utc,
)

EVALUATED_AT = datetime(
    2026,
    7,
    12,
    11,
    0,
    1,
    tzinfo=timezone.utc,
)

RATE_WINDOW_STARTED_AT = datetime(
    2026,
    7,
    12,
    11,
    0,
    0,
    tzinfo=timezone.utc,
)


class LiveRequestCountingFetcher:
    def __init__(
        self,
    ):
        self.calls = []

    def __call__(
        self,
        *,
        url,
        timeout_seconds,
    ):
        from urllib.request import Request, urlopen

        self.calls.append(
            {
                "url": url,
                "timeout_seconds": timeout_seconds,
            }
        )

        request = Request(
            url=url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "QSeries-Oracle-Live-Readiness/OLA-018"
                ),
            },
        )

        with urlopen(
            request,
            timeout=timeout_seconds,
        ) as response:
            return (
                int(response.getcode()),
                response.read().decode("utf-8"),
            )


class DeterministicHealthyFetcher:
    def __init__(
        self,
    ):
        self.calls = 0

    def __call__(
        self,
        *,
        url,
        timeout_seconds,
    ):
        self.calls += 1

        return (
            200,
            '{"markets":[],"cursor":""}',
        )


class DeterministicUnhealthyFetcher:
    def __init__(
        self,
    ):
        self.calls = 0

    def __call__(
        self,
        *,
        url,
        timeout_seconds,
    ):
        self.calls += 1

        return (
            503,
            '{"error":"source unavailable"}',
        )


def build_source_control_engine():
    return OracleAcquisitionSourceControlEngine(
        source_policies={
            "source.kalshi.market_data": (
                SourceHealthPolicy.create(
                    policy_id=(
                        "health.kalshi.live_readiness.v1"
                    ),
                    healthy_status="healthy",
                    unhealthy_status="unhealthy",
                    max_consecutive_failures=0,
                    max_latency_ms=10000,
                ),
                RateControlPolicy.create(
                    policy_id=(
                        "rate.kalshi.live_readiness.v1"
                    ),
                    max_requests_per_window=100,
                    window_seconds=60,
                    minimum_remaining_reserve=10,
                ),
            )
        }
    )


def build_rate_observation(
    *,
    requests_used=0,
):
    return RateWindowObservation.create(
        source_id="source.kalshi.market_data",
        checked_at=CHECKED_AT,
        window_started_at=RATE_WINDOW_STARTED_AT,
        requests_used=requests_used,
        metadata={
            "counter_id": (
                "kalshi.live_readiness.manual_gate"
            ),
            "readiness_probe_request_reserved": True,
        },
    )


def build_gate(
    *,
    fetcher,
):
    adapter = (
        OracleKalshiPublicMarketShadowSourceAdapter(
            market_status="open",
            page_limit=1,
            max_pages=1,
            timeout_seconds=20,
            base_url=PRODUCTION_BASE_URL,
            http_fetcher=fetcher,
        )
    )

    gate = OracleKalshiLiveReadReadinessGate(
        shadow_adapter=adapter,
        source_control_engine=(
            build_source_control_engine()
        ),
    )

    return adapter, gate


def evaluate_gate(
    *,
    gate,
    requests_used=0,
):
    return gate.evaluate(
        checked_at=CHECKED_AT,
        evaluated_at=EVALUATED_AT,
        measured_latency_ms=1,
        consecutive_failures=0,
        rate_window_observation=(
            build_rate_observation(
                requests_used=requests_used
            )
        ),
        readiness_metadata={
            "environment": "production",
            "gate_mode": "one_public_get",
            "continuous_polling": False,
        },
        replay_metadata={
            "gate": "OLA-018",
            "source": "kalshi",
        },
        audit_metadata={
            "request_id": "audit-ola-018",
        },
    )


def assert_passing_readiness(
    readiness,
):
    assert readiness.schema_version == "OLA-018"
    assert readiness.engine_id == "OLA-018"

    assert readiness.readiness_status == "passed"

    assert readiness.adapter_id == (
        "adapter.oracle.kalshi.public_markets.shadow"
    )

    assert readiness.source_id == (
        "source.kalshi.market_data"
    )

    assert readiness.source_base_url == (
        "https://external-api.kalshi.com/trade-api/v2"
    )

    assert readiness.source_endpoint == "/markets"
    assert readiness.http_method == "GET"

    assert readiness.public_endpoint is True
    assert readiness.authentication_used is False

    assert readiness.live_get_request_count == 1

    assert readiness.source_contract_valid is True

    assert (
        readiness.source_probe_health_status
        == "healthy"
    )

    assert readiness.source_reachable is True

    assert len(
        readiness.source_health_evidence_hash
    ) == 64

    assert len(
        readiness.rate_control_evidence_hash
    ) == 64

    assert len(
        readiness.source_control_decision_hash
    ) == 64

    reason_codes = set(
        readiness.source_control_reason_codes
    )

    assert "source_reachable" in reason_codes

    assert "latency_within_policy" in reason_codes

    assert (
        "consecutive_failures_within_policy"
        in reason_codes
    )

    assert (
        "rate_usage_within_limit"
        in reason_codes
    )

    assert "rate_reserve_preserved" in reason_codes

    assert "acquisition_allowed" in reason_codes

    assert (
        readiness.health_policy_evidence_present
        is True
    )

    assert readiness.rate_policy_evidence_present is True

    assert (
        readiness.source_control_acquisition_allowed
        is True
    )

    assert readiness.shadow_mode is True
    assert readiness.alerts_allowed is False
    assert readiness.qseries_intake_allowed is False

    assert (
        readiness.live_shadow_cycle_entry_ready
        is True
    )

    assert readiness.continuous_polling_started is False
    assert readiness.acquisition_performed is False

    assert (
        readiness.canonical_observation_created
        is False
    )

    assert readiness.persistence_invoked is False
    assert readiness.alert_created is False

    assert (
        readiness.qseries_intake_record_created
        is False
    )

    assert readiness.immutable is True
    assert readiness.replayable is True
    assert readiness.auditable is True
    assert readiness.explainable is True

    assert readiness.read_only is True
    assert readiness.execution_allowed is False

    assert readiness.execution_adapter_resolved is False
    assert readiness.execution_adapter_invoked is False

    assert readiness.trade_authorization_allowed is False
    assert readiness.order_placement_allowed is False
    assert readiness.funds_moved is False
    assert readiness.portfolio_mutated is False


def run_real_live_readiness_test():
    fetcher = LiveRequestCountingFetcher()

    adapter, gate = build_gate(
        fetcher=fetcher
    )

    readiness = evaluate_gate(
        gate=gate
    )

    assert len(fetcher.calls) == 1

    assert_passing_readiness(
        readiness
    )

    try:
        readiness.live_shadow_cycle_entry_ready = False

        raise AssertionError(
            "readiness record must be immutable"
        )

    except FrozenInstanceError:
        pass

    assert adapter.last_acquisition_evidence is None

    return readiness


def run_rate_fail_closed_test():
    fetcher = DeterministicHealthyFetcher()

    adapter, gate = build_gate(
        fetcher=fetcher
    )

    try:
        evaluate_gate(
            gate=gate,
            requests_used=95,
        )

        raise AssertionError(
            "insufficient rate reserve must fail closed"
        )

    except KalshiLiveReadReadinessFailure:
        pass

    assert fetcher.calls == 1

    assert adapter.last_acquisition_evidence is None


def run_unhealthy_source_fail_closed_test():
    fetcher = DeterministicUnhealthyFetcher()

    adapter, gate = build_gate(
        fetcher=fetcher
    )

    try:
        gate.evaluate(
            checked_at=CHECKED_AT,
            evaluated_at=EVALUATED_AT,
            measured_latency_ms=1,
            consecutive_failures=1,
            rate_window_observation=(
                build_rate_observation()
            ),
            readiness_metadata={},
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "unhealthy source must fail closed"
        )

    except KalshiLiveReadReadinessFailure:
        pass

    assert fetcher.calls == 1

    assert adapter.last_acquisition_evidence is None


def run_deterministic_contract_test():
    first_fetcher = DeterministicHealthyFetcher()
    second_fetcher = DeterministicHealthyFetcher()

    first_adapter, first_gate = build_gate(
        fetcher=first_fetcher
    )

    second_adapter, second_gate = build_gate(
        fetcher=second_fetcher
    )

    first = evaluate_gate(
        gate=first_gate
    )

    second = evaluate_gate(
        gate=second_gate
    )

    assert first == second

    assert first.readiness_hash == second.readiness_hash

    assert_passing_readiness(
        first
    )

    assert first_fetcher.calls == 1
    assert second_fetcher.calls == 1

    assert first_adapter.last_acquisition_evidence is None

    assert second_adapter.last_acquisition_evidence is None


def run_contract_fail_closed_tests():
    fetcher = DeterministicHealthyFetcher()

    adapter, gate = build_gate(
        fetcher=fetcher
    )

    try:
        gate.evaluate(
            checked_at=datetime(
                2026,
                7,
                12,
                11,
                0,
                0,
            ),
            evaluated_at=EVALUATED_AT,
            measured_latency_ms=1,
            consecutive_failures=0,
            rate_window_observation=(
                build_rate_observation()
            ),
            readiness_metadata={},
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "naive checked_at must fail closed"
        )

    except KalshiLiveReadReadinessContractError:
        pass

    try:
        gate.evaluate(
            checked_at=CHECKED_AT,
            evaluated_at=EVALUATED_AT,
            measured_latency_ms=-1,
            consecutive_failures=0,
            rate_window_observation=(
                build_rate_observation()
            ),
            readiness_metadata={},
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "negative latency must fail closed"
        )

    except KalshiLiveReadReadinessContractError:
        pass

    try:
        gate.evaluate(
            checked_at=CHECKED_AT,
            evaluated_at=EVALUATED_AT,
            measured_latency_ms=1,
            consecutive_failures=0,
            rate_window_observation=(
                build_rate_observation()
            ),
            readiness_metadata={
                "api_key": "must-not-enter-evidence",
            },
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "secret metadata must fail closed"
        )

    except KalshiLiveReadReadinessContractError:
        pass

    assert adapter.last_acquisition_evidence is None


def main():
    readiness = run_real_live_readiness_test()

    run_rate_fail_closed_test()

    run_unhealthy_source_fail_closed_test()

    run_deterministic_contract_test()

    run_contract_fail_closed_tests()

    result = {
        "schema_version": readiness.schema_version,
        "engine_id": readiness.engine_id,
        "status": "passed",
        "readiness_status": readiness.readiness_status,
        "adapter_id": readiness.adapter_id,
        "source_id": readiness.source_id,
        "source_base_url": readiness.source_base_url,
        "source_endpoint": readiness.source_endpoint,
        "http_method": readiness.http_method,
        "public_endpoint": readiness.public_endpoint,
        "authentication_used": (
            readiness.authentication_used
        ),
        "live_get_request_count": (
            readiness.live_get_request_count
        ),
        "real_public_request_completed": True,
        "source_contract_valid": (
            readiness.source_contract_valid
        ),
        "source_probe_health_status": (
            readiness.source_probe_health_status
        ),
        "source_reachable": readiness.source_reachable,
        "ola_002_parent_decision_contract_consumed": True,
        "ola_002_child_health_identity_hash_only": True,
        "ola_002_child_rate_identity_hash_only": True,
        "ola_002_reason_codes_consumed": True,
        "health_policy_evidence_present": (
            readiness.health_policy_evidence_present
        ),
        "rate_policy_evidence_present": (
            readiness.rate_policy_evidence_present
        ),
        "ola_002_source_control_allowed": (
            readiness.source_control_acquisition_allowed
        ),
        "rate_reserve_failure_blocked": True,
        "unhealthy_source_blocked": True,
        "deterministic_readiness_hashing": True,
        "shadow_mode": readiness.shadow_mode,
        "alerts_allowed": readiness.alerts_allowed,
        "qseries_intake_allowed": (
            readiness.qseries_intake_allowed
        ),
        "live_shadow_cycle_entry_ready": (
            readiness.live_shadow_cycle_entry_ready
        ),
        "continuous_polling_started": (
            readiness.continuous_polling_started
        ),
        "acquisition_performed": (
            readiness.acquisition_performed
        ),
        "canonical_observation_created": (
            readiness.canonical_observation_created
        ),
        "persistence_invoked": (
            readiness.persistence_invoked
        ),
        "alert_created": readiness.alert_created,
        "qseries_intake_record_created": (
            readiness.qseries_intake_record_created
        ),
        "read_only": readiness.read_only,
        "execution_allowed": readiness.execution_allowed,
        "execution_adapter_resolved": (
            readiness.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            readiness.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            readiness.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            readiness.order_placement_allowed
        ),
        "funds_moved": readiness.funds_moved,
        "portfolio_mutated": readiness.portfolio_mutated,
    }

    print(
        "[PASS] OLA-018 Oracle Kalshi Live Read "
        "Readiness Gate"
    )

    print(result)


if __name__ == "__main__":
    main()
