from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

TEST_PATH = (
    ROOT
    / "test_int_ola_smoke_001_oracle_live_acquisition_smoke_gate.py"
)


TEST_CONTENT = r'''
"""
INT-OLA-SMOKE-001
Oracle Live Acquisition OLA-001 Through OLA-005 Smoke Integration Gate

Required five-build subsystem checkpoint.

Validated chain:

OLA-002 SOURCE CONTROL
    |
OLA-001 ACQUISITION
    |
OLA-003 DEDUPLICATION
    |
OLA-004 MARKET IDENTITY / VENUE RESOLUTION
    |
OLA-005 VALIDITY / EXPIRATION

This gate proves:

- source health and rate evidence can authorize acquisition,
- OLA-001 accepts OLA-002 evidence,
- OLA-003 satisfies the OLA-001 deduplication hook,
- duplicate observations are not routed twice,
- canonical observations can produce market identity evidence,
- OLA-004 resolves an approved venue deterministically,
- unresolved and guessed venues are not introduced,
- OLA-005 accepts the verified market/venue identity,
- active and expired opportunity states remain explicit,
- every integrated layer remains read-only,
- no trade authorization is introduced,
- no execution adapter is resolved or invoked,
- no funds are moved,
- no portfolio is mutated.
"""

from datetime import datetime, timezone
from decimal import Decimal


from qseries_v2.oracle_intelligence.live_acquisition import (
    ApprovedVenueRegistration,
    CanonicalObservation,
    DeduplicationEvidence,
    ObservationRoutingEvidence,
    OpportunityValidityRequest,
    OracleAcquisitionDeduplicationLedger,
    OracleAcquisitionSourceControlEngine,
    OracleCanonicalMarketIdentityVenueResolutionEngine,
    OracleCanonicalOpportunityValidityExpirationEngine,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlPolicy,
    RateWindowObservation,
    RawSourceObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
    SourceMarketIdentityEvidence,
)


SCHEMA_VERSION = "INT-OLA-SMOKE-001"
ENGINE_ID = "INT-OLA-SMOKE-001"


HEALTH_CHECKED_AT = datetime(
    2026,
    7,
    11,
    22,
    29,
    50,
    tzinfo=timezone.utc,
)

RATE_WINDOW_STARTED_AT = datetime(
    2026,
    7,
    11,
    22,
    29,
    0,
    tzinfo=timezone.utc,
)

CONTROL_EVALUATED_AT = datetime(
    2026,
    7,
    11,
    22,
    29,
    55,
    tzinfo=timezone.utc,
)

OBSERVED_AT = datetime(
    2026,
    7,
    11,
    22,
    29,
    56,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    11,
    22,
    30,
    0,
    tzinfo=timezone.utc,
)

VENUE_RESOLVED_AT = datetime(
    2026,
    7,
    11,
    22,
    30,
    1,
    tzinfo=timezone.utc,
)

VALID_FROM = datetime(
    2026,
    7,
    11,
    22,
    30,
    2,
    tzinfo=timezone.utc,
)

ACTIVE_EVALUATED_AT = datetime(
    2026,
    7,
    11,
    22,
    31,
    0,
    tzinfo=timezone.utc,
)

EXPIRES_AT = datetime(
    2026,
    7,
    11,
    22,
    40,
    0,
    tzinfo=timezone.utc,
)

EXPIRED_EVALUATED_AT = datetime(
    2026,
    7,
    11,
    22,
    40,
    0,
    tzinfo=timezone.utc,
)


class SmokeKalshiReadOnlyAdapter:
    adapter_id = "adapter.oracle.smoke.kalshi"
    source_id = "source.kalshi.market_data"
    read_only = True
    execution_allowed = False

    def acquire(
        self,
        *,
        acquired_at,
    ):
        assert acquired_at == ACQUIRED_AT

        first = RawSourceObservation.create(
            source_observation_id=(
                "KXBTC-26JUL11-116000.snapshot.001"
            ),
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "source_market_id": (
                    "KXBTC-26JUL11-116000"
                ),
                "source_symbol": (
                    "KXBTC-26JUL11-116000"
                ),
                "instrument_type": (
                    "prediction_contract"
                ),
                "market_title": (
                    "Bitcoin below 116000 by 5 PM"
                ),
                "venue_claim": "venue.kalshi",
                "share_side": "yes",
                "share_price": Decimal("0.31"),
                "oracle_fair_value": Decimal("0.48"),
            },
            provenance={
                "adapter_id": (
                    "adapter.oracle.smoke.kalshi"
                ),
                "source_id": (
                    "source.kalshi.market_data"
                ),
                "transport": "smoke_test",
                "endpoint_family": "markets",
            },
        )

        duplicate = RawSourceObservation.create(
            source_observation_id=(
                "KXBTC-26JUL11-116000.snapshot.001"
            ),
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "source_market_id": (
                    "KXBTC-26JUL11-116000"
                ),
                "source_symbol": (
                    "KXBTC-26JUL11-116000"
                ),
                "instrument_type": (
                    "prediction_contract"
                ),
                "market_title": (
                    "Bitcoin below 116000 by 5 PM"
                ),
                "venue_claim": "venue.kalshi",
                "share_side": "yes",
                "share_price": Decimal("0.31"),
                "oracle_fair_value": Decimal("0.48"),
            },
            provenance={
                "adapter_id": (
                    "adapter.oracle.smoke.kalshi"
                ),
                "source_id": (
                    "source.kalshi.market_data"
                ),
                "transport": "smoke_test",
                "endpoint_family": "markets",
            },
        )

        return (
            first,
            duplicate,
        )


class SmokeCanonicalObservationRouter:
    def __init__(self):
        self.routed_observation_ids = []

    def __call__(
        self,
        observation,
        routed_at,
    ):
        self.routed_observation_ids.append(
            observation.observation_id
        )

        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            route_id=(
                "oracle.smoke.canonical.observation.router"
            ),
            routed_at=routed_at,
            accepted=True,
            metadata={
                "destination": (
                    "oracle.smoke.identity_resolution"
                ),
                "persistence_required": True,
            },
        )


def build_source_control_engine():
    health_policy = SourceHealthPolicy.create(
        policy_id="health.kalshi.smoke.v1",
        healthy_status="healthy",
        unhealthy_status="unhealthy",
        max_consecutive_failures=0,
        max_latency_ms=500,
    )

    rate_policy = RateControlPolicy.create(
        policy_id="rate.kalshi.smoke.v1",
        max_requests_per_window=100,
        window_seconds=60,
        minimum_remaining_reserve=10,
    )

    return OracleAcquisitionSourceControlEngine(
        source_policies={
            "source.kalshi.market_data": (
                health_policy,
                rate_policy,
            )
        }
    )


def build_source_control_decision():
    engine = build_source_control_engine()

    health_observation = SourceHealthObservation.create(
        source_id="source.kalshi.market_data",
        checked_at=HEALTH_CHECKED_AT,
        reachable=True,
        consecutive_failures=0,
        latency_ms=48,
        metadata={
            "probe_id": "probe.ola.smoke.001",
            "transport": "https",
        },
    )

    rate_observation = RateWindowObservation.create(
        source_id="source.kalshi.market_data",
        checked_at=HEALTH_CHECKED_AT,
        window_started_at=RATE_WINDOW_STARTED_AT,
        requests_used=20,
        metadata={
            "counter_id": "rate.ola.smoke.001",
        },
    )

    return engine.evaluate(
        health_observation=health_observation,
        rate_observation=rate_observation,
        evaluated_at=CONTROL_EVALUATED_AT,
        replay_metadata={
            "integration_gate": ENGINE_ID,
            "phase": "source_control",
        },
        audit_metadata={
            "request_id": "audit-int-ola-smoke-001",
        },
    )


def build_acquisition_runtime():
    ledger = OracleAcquisitionDeduplicationLedger(
        policy_id="oracle.dedup.content_hash.v1",
        entry_metadata={
            "integration_gate": ENGINE_ID,
            "persistence_required": True,
        },
    )

    router = SmokeCanonicalObservationRouter()

    runtime = OracleLiveReadOnlyAcquisitionRuntime(
        approved_adapters=(
            SmokeKalshiReadOnlyAdapter(),
        ),
        deduplication_hook=ledger,
        canonical_observation_router=router,
    )

    return runtime, ledger, router


def extract_first_canonical_observation(
    acquisition_record,
):
    for record in acquisition_record.observations:
        if not record.deduplication.duplicate:
            return record.observation

    raise AssertionError(
        "smoke acquisition did not produce canonical observation"
    )


def build_market_identity_evidence(
    observation,
):
    payload = dict(observation.payload)

    return SourceMarketIdentityEvidence.create(
        source_id=observation.source_id,
        source_market_id=payload[
            "source_market_id"
        ],
        source_symbol=payload[
            "source_symbol"
        ],
        instrument_type=payload[
            "instrument_type"
        ],
        market_title=payload[
            "market_title"
        ],
        venue_claim=payload[
            "venue_claim"
        ],
        identity_metadata={
            "share_side": payload["share_side"],
            "share_price": payload["share_price"],
            "oracle_fair_value": payload[
                "oracle_fair_value"
            ],
            "canonical_observation_id": (
                observation.observation_id
            ),
            "content_hash": observation.content_hash,
        },
        observed_at=observation.observed_at,
    )


def build_venue_resolution_engine():
    kalshi = ApprovedVenueRegistration.create(
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        source_ids=(
            "source.kalshi.market_data",
        ),
        registration_metadata={
            "approved": True,
            "canonical_identity_required": True,
            "execution_adapter_mapping_owned_by": (
                "qseries"
            ),
        },
    )

    coinbase = ApprovedVenueRegistration.create(
        venue_id="venue.coinbase",
        venue_name="Coinbase",
        venue_type="crypto_spot",
        source_ids=(
            "source.coinbase.market_data",
        ),
        registration_metadata={
            "approved": True,
            "canonical_identity_required": True,
            "execution_adapter_mapping_owned_by": (
                "qseries"
            ),
        },
    )

    return (
        OracleCanonicalMarketIdentityVenueResolutionEngine(
            approved_venues=(
                kalshi,
                coinbase,
            )
        )
    )


def build_validity_request(
    market_venue_record,
):
    identity = (
        market_venue_record.canonical_market_identity
    )

    venue = market_venue_record.venue_resolution

    assert venue.venue_verified is True
    assert venue.venue_id is not None

    return OpportunityValidityRequest.create(
        opportunity_id=(
            "opportunity."
            + identity.canonical_market_id.removeprefix(
                "market."
            )
        ),
        canonical_market_id=identity.canonical_market_id,
        venue_id=venue.venue_id,
        opportunity_type="prediction_market",
        observed_at=identity.observed_at,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_policy_id=(
            "oracle.validity.prediction_market.smoke.v1"
        ),
        source_record_hash=(
            market_venue_record.record_hash
        ),
        metadata={
            "share_side": "yes",
            "share_price": "0.31",
            "oracle_fair_value": "0.48",
            "display_date_required": True,
            "display_time_required": True,
            "display_venue_required": True,
        },
    )


def assert_no_execution_invariants(
    *,
    source_control,
    acquisition,
    market_venue,
    active_validity,
    expired_validity,
):
    assert source_control.read_only is True
    assert source_control.execution_allowed is False
    assert (
        source_control.acquisition_performed
        is False
    )
    assert (
        source_control.trade_authorization_allowed
        is False
    )
    assert (
        source_control.order_placement_allowed
        is False
    )
    assert (
        source_control
        .execution_adapter_invocation_allowed
        is False
    )
    assert source_control.funds_moved is False
    assert source_control.portfolio_mutated is False

    assert acquisition.read_only is True
    assert acquisition.execution_allowed is False
    assert (
        acquisition.trade_authorization_allowed
        is False
    )
    assert (
        acquisition.order_placement_allowed
        is False
    )
    assert (
        acquisition
        .execution_adapter_invocation_allowed
        is False
    )
    assert acquisition.funds_moved is False
    assert acquisition.portfolio_mutated is False

    assert market_venue.read_only is True
    assert market_venue.execution_allowed is False
    assert (
        market_venue.trade_authorization_allowed
        is False
    )
    assert (
        market_venue.order_placement_allowed
        is False
    )
    assert (
        market_venue
        .execution_adapter_invocation_allowed
        is False
    )
    assert market_venue.funds_moved is False
    assert market_venue.portfolio_mutated is False

    for validity in (
        active_validity,
        expired_validity,
    ):
        assert validity.read_only is True
        assert validity.execution_allowed is False
        assert (
            validity.trade_authorization_allowed
            is False
        )
        assert (
            validity.order_placement_allowed
            is False
        )
        assert (
            validity
            .execution_adapter_invocation_allowed
            is False
        )
        assert validity.funds_moved is False
        assert validity.portfolio_mutated is False


def run_integrated_smoke_gate():
    source_control = build_source_control_decision()

    assert source_control.acquisition_allowed is True
    assert (
        source_control.health_evidence.status
        == "healthy"
    )
    assert (
        source_control.rate_control_evidence.allowed
        is True
    )

    runtime, ledger, router = build_acquisition_runtime()

    acquisition = runtime.acquire(
        adapter_id="adapter.oracle.smoke.kalshi",
        acquired_at=ACQUIRED_AT,
        health_evidence=source_control.health_evidence,
        rate_control_evidence=(
            source_control.rate_control_evidence
        ),
        replay_metadata={
            "integration_gate": ENGINE_ID,
            "phase": "acquisition",
        },
        audit_metadata={
            "request_id": "audit-int-ola-smoke-001",
        },
    )

    assert acquisition.status == "passed"
    assert acquisition.observation_count == 2
    assert acquisition.canonical_count == 1
    assert acquisition.duplicate_count == 1
    assert acquisition.routed_count == 1

    assert ledger.entry_count == 1

    assert len(router.routed_observation_ids) == 1

    first_record = acquisition.observations[0]
    duplicate_record = acquisition.observations[1]

    assert (
        first_record.deduplication.duplicate
        is False
    )

    assert (
        duplicate_record.deduplication.duplicate
        is True
    )

    assert first_record.routing is not None
    assert duplicate_record.routing is None

    canonical_observation = (
        extract_first_canonical_observation(
            acquisition
        )
    )

    assert isinstance(
        canonical_observation,
        CanonicalObservation,
    )

    identity_evidence = build_market_identity_evidence(
        canonical_observation
    )

    venue_engine = build_venue_resolution_engine()

    market_venue = venue_engine.resolve(
        evidence=identity_evidence,
        resolved_at=VENUE_RESOLVED_AT,
    )

    identity = (
        market_venue.canonical_market_identity
    )

    venue = market_venue.venue_resolution

    assert identity.source_market_id == (
        "KXBTC-26JUL11-116000"
    )

    assert identity.source_symbol == (
        "KXBTC-26JUL11-116000"
    )

    assert identity.instrument_type == (
        "prediction_contract"
    )

    assert venue.resolution_status == "verified"
    assert venue.venue_verified is True
    assert venue.venue_id == "venue.kalshi"
    assert venue.venue_name == "Kalshi"
    assert venue.venue_type == "prediction_market"

    assert venue.default_venue_used is False
    assert venue.fallback_adapter_used is False

    assert (
        venue.execution_adapter_resolved
        is False
    )

    validity_request = build_validity_request(
        market_venue
    )

    validity_engine = (
        OracleCanonicalOpportunityValidityExpirationEngine()
    )

    active_validity = validity_engine.evaluate(
        request=validity_request,
        evaluated_at=ACTIVE_EVALUATED_AT,
        replay_metadata={
            "integration_gate": ENGINE_ID,
            "phase": "validity_active",
        },
        audit_metadata={
            "request_id": "audit-int-ola-smoke-001",
        },
    )

    expired_validity = validity_engine.evaluate(
        request=validity_request,
        evaluated_at=EXPIRED_EVALUATED_AT,
        replay_metadata={
            "integration_gate": ENGINE_ID,
            "phase": "validity_expired",
        },
        audit_metadata={
            "request_id": "audit-int-ola-smoke-001",
        },
    )

    assert active_validity.active is True
    assert active_validity.expired is False
    assert (
        active_validity.validity_status
        == "active"
    )
    assert (
        active_validity.freshness_status
        == "fresh"
    )

    assert expired_validity.active is False
    assert expired_validity.expired is True
    assert (
        expired_validity.validity_status
        == "expired"
    )
    assert (
        expired_validity.freshness_status
        == "expired"
    )

    assert (
        active_validity.canonical_market_id
        == identity.canonical_market_id
    )

    assert (
        active_validity.venue_id
        == venue.venue_id
    )

    assert (
        active_validity.source_record_hash
        == market_venue.record_hash
    )

    assert (
        active_validity.observed_at
        == identity.observed_at
    )

    assert (
        active_validity.valid_from
        == VALID_FROM
    )

    assert (
        active_validity.expires_at
        == EXPIRES_AT
    )

    assert (
        expired_validity.expires_at
        == EXPIRES_AT
    )

    assert_no_execution_invariants(
        source_control=source_control,
        acquisition=acquisition,
        market_venue=market_venue,
        active_validity=active_validity,
        expired_validity=expired_validity,
    )

    return {
        "source_control": source_control,
        "acquisition": acquisition,
        "ledger": ledger,
        "router": router,
        "market_venue": market_venue,
        "active_validity": active_validity,
        "expired_validity": expired_validity,
    }


def run_deterministic_replay_test():
    first = run_integrated_smoke_gate()
    second = run_integrated_smoke_gate()

    assert (
        first["source_control"].decision_hash
        == second["source_control"].decision_hash
    )

    assert (
        first["acquisition"].batch_hash
        == second["acquisition"].batch_hash
    )

    assert (
        first["market_venue"].record_hash
        == second["market_venue"].record_hash
    )

    assert (
        first["active_validity"]
        .validity_evidence_hash
        == second["active_validity"]
        .validity_evidence_hash
    )

    assert (
        first["expired_validity"]
        .validity_evidence_hash
        == second["expired_validity"]
        .validity_evidence_hash
    )

    return first


def main():
    result = run_deterministic_replay_test()

    source_control = result["source_control"]
    acquisition = result["acquisition"]
    ledger = result["ledger"]
    market_venue = result["market_venue"]
    active_validity = result["active_validity"]
    expired_validity = result["expired_validity"]

    output = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "ola_001_acquisition_passed": (
            acquisition.status == "passed"
        ),
        "ola_002_source_control_passed": (
            source_control.acquisition_allowed
            is True
        ),
        "ola_003_deduplication_passed": (
            acquisition.duplicate_count == 1
            and ledger.entry_count == 1
        ),
        "ola_004_identity_venue_passed": (
            market_venue
            .venue_resolution
            .venue_verified
            is True
        ),
        "ola_005_validity_expiration_passed": (
            active_validity.active is True
            and expired_validity.expired is True
        ),
        "source_id": acquisition.source_id,
        "adapter_id": acquisition.adapter_id,
        "observation_count": (
            acquisition.observation_count
        ),
        "canonical_count": (
            acquisition.canonical_count
        ),
        "duplicate_count": (
            acquisition.duplicate_count
        ),
        "routed_count": acquisition.routed_count,
        "canonical_market_id": (
            market_venue
            .canonical_market_identity
            .canonical_market_id
        ),
        "source_market_id": (
            market_venue
            .canonical_market_identity
            .source_market_id
        ),
        "venue_id": (
            market_venue
            .venue_resolution
            .venue_id
        ),
        "venue_verified": (
            market_venue
            .venue_resolution
            .venue_verified
        ),
        "default_venue_used": (
            market_venue
            .venue_resolution
            .default_venue_used
        ),
        "fallback_adapter_used": (
            market_venue
            .venue_resolution
            .fallback_adapter_used
        ),
        "execution_adapter_resolved": (
            market_venue
            .venue_resolution
            .execution_adapter_resolved
        ),
        "active_validity_status": (
            active_validity.validity_status
        ),
        "expired_validity_status": (
            expired_validity.validity_status
        ),
        "explicit_valid_from": (
            active_validity.valid_from.isoformat()
        ),
        "explicit_expires_at": (
            active_validity.expires_at.isoformat()
        ),
        "deterministic_replay_passed": True,
        "read_only": True,
        "execution_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "execution_adapter_invocation_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    print(
        "[PASS] INT-OLA-SMOKE-001 "
        "Oracle Live Acquisition OLA-001 Through "
        "OLA-005 Smoke Integration Gate"
    )

    print(output)


if __name__ == "__main__":
    main()
'''


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] Wrote {path}")


def main() -> None:
    print("========================================")
    print(" INT-OLA-SMOKE-001 INSTALLER")
    print(" Oracle Live Acquisition")
    print(" OLA-001 Through OLA-005")
    print(" Smoke Integration Gate")
    print("========================================")

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    print()
    print(
        "[DONE] INT-OLA-SMOKE-001 installed"
    )
    print()
    print("Run:")
    print(
        "py test_int_ola_smoke_001_"
        "oracle_live_acquisition_smoke_gate.py"
    )


if __name__ == "__main__":
    main()