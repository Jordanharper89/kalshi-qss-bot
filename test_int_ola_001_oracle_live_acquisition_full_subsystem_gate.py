"""
INT-OLA-001
Oracle Live Acquisition Full Subsystem Integration Gate

Full OLA-001 through OLA-010 subsystem checkpoint.

Validated architecture:

SOURCE
    |
OLA-002 SOURCE HEALTH / RATE CONTROL
    |
OLA-010 CONTROLLED ACQUISITION CYCLE
    |
OLA-001 LIVE READ-ONLY ACQUISITION
    |
OLA-003 DEDUPLICATION
    |
OLA-009 PERSISTENCE ROUTER
    |
OLA-008 APPEND-ONLY PERSISTENCE LEDGER
    |
OLA-004 CANONICAL MARKET IDENTITY / VENUE RESOLUTION
    |
OLA-005 VALIDITY / EXPIRATION
    |
OLA-006 CROSS-VENUE OPPORTUNITY COMPARISON
    |
OLA-007 CANONICAL OPPORTUNITY ALERT RECORD

This gate proves:

- source-control permission is required before acquisition,
- blocked source control does not invoke an adapter,
- canonical observations are deterministically created,
- duplicate canonical observations do not route,
- non-duplicate observations persist before routing acceptance,
- persistence entries form an append-only deterministic chain,
- canonical market identity is preserved,
- source-native market identity is preserved,
- venue resolution is explicit and verified,
- no default venue is used,
- no fallback execution adapter is used,
- opportunity validity is explicit,
- expired opportunities are excluded,
- unlike instrument raw prices are not directly compared,
- normalized cross-venue comparison resolves intelligence only,
- the selected alert preserves the winning venue-specific price,
- date/time and expiration evidence are explicit,
- deterministic replay reproduces canonical hashes,
- Oracle remains permanently read-only,
- no execution adapter is resolved,
- no execution adapter is invoked,
- no trade is authorized,
- no order is placed,
- no funds are moved,
- no portfolio is mutated.
"""

from datetime import datetime, timezone
from decimal import Decimal


from qseries_v2.oracle_intelligence.live_acquisition import (
    ApprovedVenueRegistration,
    ComparisonScoringPolicy,
    CrossVenueOpportunityCandidate,
    OpportunityValidityRequest,
    OracleAcquisitionDeduplicationLedger,
    OracleAcquisitionSourceControlEngine,
    OracleCanonicalCrossVenueOpportunityComparisonEngine,
    OracleCanonicalMarketIdentityVenueResolutionEngine,
    OracleCanonicalObservationPersistenceLedger,
    OracleCanonicalObservationPersistenceRouter,
    OracleCanonicalOpportunityAlertRecordEngine,
    OracleCanonicalOpportunityValidityExpirationEngine,
    OracleControlledAcquisitionCycleOrchestrator,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlPolicy,
    RateWindowObservation,
    RawSourceObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
    SourceMarketIdentityEvidence,
)


SCHEMA_VERSION = "INT-OLA-001"
ENGINE_ID = "INT-OLA-001"


CONTROL_CHECKED_AT = datetime(
    2026,
    7,
    12,
    1,
    0,
    50,
    tzinfo=timezone.utc,
)

RATE_WINDOW_STARTED_AT = datetime(
    2026,
    7,
    12,
    1,
    0,
    0,
    tzinfo=timezone.utc,
)

CONTROL_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    1,
    0,
    55,
    tzinfo=timezone.utc,
)

OBSERVED_AT = datetime(
    2026,
    7,
    12,
    1,
    0,
    58,
    tzinfo=timezone.utc,
)

CYCLE_STARTED_AT = datetime(
    2026,
    7,
    12,
    1,
    1,
    0,
    tzinfo=timezone.utc,
)

CYCLE_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    1,
    1,
    2,
    tzinfo=timezone.utc,
)

VENUE_RESOLVED_AT = datetime(
    2026,
    7,
    12,
    1,
    1,
    3,
    tzinfo=timezone.utc,
)

VALID_FROM = datetime(
    2026,
    7,
    12,
    1,
    1,
    5,
    tzinfo=timezone.utc,
)

VALIDITY_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    1,
    2,
    0,
    tzinfo=timezone.utc,
)

COMPARE_AT = datetime(
    2026,
    7,
    12,
    1,
    2,
    1,
    tzinfo=timezone.utc,
)

ALERT_CREATED_AT = datetime(
    2026,
    7,
    12,
    1,
    2,
    2,
    tzinfo=timezone.utc,
)

EXPIRES_AT = datetime(
    2026,
    7,
    12,
    1,
    12,
    0,
    tzinfo=timezone.utc,
)

EXPIRED_AT = datetime(
    2026,
    7,
    12,
    1,
    12,
    0,
    tzinfo=timezone.utc,
)


class FullGateKalshiAdapter:
    adapter_id = "adapter.oracle.fullgate.kalshi"
    source_id = "source.kalshi.market_data"
    read_only = True
    execution_allowed = False

    def __init__(self):
        self.acquire_call_count = 0

    def acquire(
        self,
        *,
        acquired_at,
    ):
        self.acquire_call_count += 1

        assert acquired_at == CYCLE_STARTED_AT

        first = RawSourceObservation.create(
            source_observation_id=(
                "KXBTC-26JUL12-116000.snapshot.001"
            ),
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "source_market_id": (
                    "KXBTC-26JUL12-116000"
                ),
                "source_symbol": (
                    "KXBTC-26JUL12-116000"
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
                "volume": 1250,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
                "transport": "integration_test",
                "endpoint_family": "markets",
            },
        )

        duplicate = RawSourceObservation.create(
            source_observation_id=(
                "KXBTC-26JUL12-116000.snapshot.001"
            ),
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "source_market_id": (
                    "KXBTC-26JUL12-116000"
                ),
                "source_symbol": (
                    "KXBTC-26JUL12-116000"
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
                "volume": 1250,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
                "transport": "integration_test",
                "endpoint_family": "markets",
            },
        )

        second = RawSourceObservation.create(
            source_observation_id=(
                "KXBTC-26JUL12-117000.snapshot.001"
            ),
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "source_market_id": (
                    "KXBTC-26JUL12-117000"
                ),
                "source_symbol": (
                    "KXBTC-26JUL12-117000"
                ),
                "instrument_type": (
                    "prediction_contract"
                ),
                "market_title": (
                    "Bitcoin below 117000 by 5 PM"
                ),
                "venue_claim": "venue.kalshi",
                "share_side": "yes",
                "share_price": Decimal("0.44"),
                "oracle_fair_value": Decimal("0.54"),
                "volume": 1800,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
                "transport": "integration_test",
                "endpoint_family": "markets",
            },
        )

        return (
            first,
            duplicate,
            second,
        )


def build_source_control_engine():
    health_policy = SourceHealthPolicy.create(
        policy_id="health.kalshi.fullgate.v1",
        healthy_status="healthy",
        unhealthy_status="unhealthy",
        max_consecutive_failures=0,
        max_latency_ms=500,
    )

    rate_policy = RateControlPolicy.create(
        policy_id="rate.kalshi.fullgate.v1",
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


def build_source_control_decision(
    *,
    healthy,
):
    health_observation = SourceHealthObservation.create(
        source_id="source.kalshi.market_data",
        checked_at=CONTROL_CHECKED_AT,
        reachable=healthy,
        consecutive_failures=(
            0
            if healthy
            else 1
        ),
        latency_ms=(
            42
            if healthy
            else None
        ),
        metadata={
            "probe_id": "probe.int.ola.001",
            "transport": "https",
        },
    )

    rate_observation = RateWindowObservation.create(
        source_id="source.kalshi.market_data",
        checked_at=CONTROL_CHECKED_AT,
        window_started_at=RATE_WINDOW_STARTED_AT,
        requests_used=20,
        metadata={
            "counter_id": "rate.int.ola.001",
        },
    )

    return build_source_control_engine().evaluate(
        health_observation=health_observation,
        rate_observation=rate_observation,
        evaluated_at=CONTROL_EVALUATED_AT,
        replay_metadata={
            "integration_gate": ENGINE_ID,
            "phase": "source_control",
        },
        audit_metadata={
            "request_id": "audit-int-ola-001-control",
        },
    )


def build_acquisition_system():
    adapter = FullGateKalshiAdapter()

    deduplication_ledger = (
        OracleAcquisitionDeduplicationLedger(
            policy_id="oracle.dedup.content_hash.v1",
            entry_metadata={
                "integration_gate": ENGINE_ID,
                "retention_required": True,
            },
        )
    )

    persistence_ledger = (
        OracleCanonicalObservationPersistenceLedger()
    )

    persistence_router = (
        OracleCanonicalObservationPersistenceRouter(
            persistence_ledger=persistence_ledger,
            route_id=(
                "oracle.canonical.persistence.router.int.ola.001"
            ),
            persistence_metadata={
                "persistence_policy_id": (
                    "oracle.persistence.canonical.v1"
                ),
                "integration_gate": ENGINE_ID,
                "retention_required": True,
            },
            replay_metadata={
                "integration_gate": ENGINE_ID,
                "phase": "persistence_routing",
            },
            audit_metadata={
                "request_id": (
                    "audit-int-ola-001-router"
                ),
            },
        )
    )

    runtime = OracleLiveReadOnlyAcquisitionRuntime(
        approved_adapters=(
            adapter,
        ),
        deduplication_hook=deduplication_ledger,
        canonical_observation_router=persistence_router,
    )

    orchestrator = (
        OracleControlledAcquisitionCycleOrchestrator(
            acquisition_runtime=runtime,
            persistence_router=persistence_router,
        )
    )

    return {
        "adapter": adapter,
        "deduplication_ledger": deduplication_ledger,
        "persistence_ledger": persistence_ledger,
        "persistence_router": persistence_router,
        "runtime": runtime,
        "orchestrator": orchestrator,
    }


def run_controlled_acquisition_path():
    system = build_acquisition_system()

    decision = build_source_control_decision(
        healthy=True
    )

    assert decision.acquisition_allowed is True

    cycle = system["orchestrator"].run_cycle(
        adapter_id="adapter.oracle.fullgate.kalshi",
        source_control_decision=decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "integration_gate": ENGINE_ID,
            "phase": "controlled_acquisition_cycle",
        },
        audit_metadata={
            "request_id": "audit-int-ola-001-cycle",
        },
    )

    assert cycle.cycle_status == "completed"
    assert cycle.acquisition_invoked is True

    assert cycle.observation_count == 3
    assert cycle.canonical_count == 2
    assert cycle.duplicate_count == 1
    assert cycle.routed_count == 2
    assert cycle.persisted_count == 2

    assert (
        system["adapter"].acquire_call_count
        == 1
    )

    assert (
        system["deduplication_ledger"].entry_count
        == 2
    )

    assert (
        system["persistence_ledger"].entry_count
        == 2
    )

    assert (
        system["persistence_router"]
        .routing_record_count
        == 2
    )

    assert (
        cycle.persistence_terminal_chain_hash
        == system["persistence_ledger"]
        .terminal_chain_hash
    )

    return system, decision, cycle


def run_blocked_source_control_path():
    system = build_acquisition_system()

    decision = build_source_control_decision(
        healthy=False
    )

    assert decision.acquisition_allowed is False

    cycle = system["orchestrator"].run_cycle(
        adapter_id="adapter.oracle.fullgate.kalshi",
        source_control_decision=decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "integration_gate": ENGINE_ID,
            "phase": "blocked_cycle",
        },
        audit_metadata={
            "request_id": (
                "audit-int-ola-001-blocked-cycle"
            ),
        },
    )

    assert cycle.cycle_status == "blocked"

    assert cycle.acquisition_invoked is False

    assert system["adapter"].acquire_call_count == 0

    assert (
        system["deduplication_ledger"].entry_count
        == 0
    )

    assert (
        system["persistence_ledger"].entry_count
        == 0
    )

    assert (
        system["persistence_router"]
        .routing_record_count
        == 0
    )

    return system, decision, cycle


def get_persisted_observation(
    *,
    system,
    source_market_id,
):
    for observation_id in (
        system["persistence_ledger"].observation_ids
    ):
        entry = system["persistence_ledger"].get_entry(
            observation_id=observation_id
        )

        assert entry is not None

        payload = dict(
            entry.canonical_observation.payload
        )

        if (
            payload["source_market_id"]
            == source_market_id
        ):
            return entry.canonical_observation

    raise AssertionError(
        "requested persisted observation was not found"
    )


def build_identity_engine():
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


def build_market_venue_record(
    observation,
):
    payload = dict(observation.payload)

    evidence = SourceMarketIdentityEvidence.create(
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
            "canonical_observation_id": (
                observation.observation_id
            ),
            "content_hash": observation.content_hash,
            "share_side": payload["share_side"],
            "share_price": payload["share_price"],
            "oracle_fair_value": payload[
                "oracle_fair_value"
            ],
        },
        observed_at=observation.observed_at,
    )

    return build_identity_engine().resolve(
        evidence=evidence,
        resolved_at=VENUE_RESOLVED_AT,
    )


def build_validity_evidence(
    *,
    market_venue_record,
    opportunity_id,
):
    identity = (
        market_venue_record.canonical_market_identity
    )

    venue = market_venue_record.venue_resolution

    assert venue.venue_verified is True
    assert venue.venue_id is not None

    request = OpportunityValidityRequest.create(
        opportunity_id=opportunity_id,
        canonical_market_id=identity.canonical_market_id,
        venue_id=venue.venue_id,
        opportunity_type="prediction_market",
        observed_at=identity.observed_at,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_policy_id=(
            "oracle.validity.prediction_market.int.ola.001"
        ),
        source_record_hash=(
            market_venue_record.record_hash
        ),
        metadata={
            "integration_gate": ENGINE_ID,
            "date_required": True,
            "time_required": True,
            "expiration_required": True,
        },
    )

    return (
        OracleCanonicalOpportunityValidityExpirationEngine()
        .evaluate(
            request=request,
            evaluated_at=VALIDITY_EVALUATED_AT,
            replay_metadata={
                "integration_gate": ENGINE_ID,
                "phase": "validity",
            },
            audit_metadata={
                "request_id": (
                    "audit-int-ola-001-validity"
                ),
            },
        )
    )


def build_expired_validity_evidence(
    *,
    market_venue_record,
    opportunity_id,
):
    identity = (
        market_venue_record.canonical_market_identity
    )

    venue = market_venue_record.venue_resolution

    assert venue.venue_id is not None

    request = OpportunityValidityRequest.create(
        opportunity_id=opportunity_id,
        canonical_market_id=identity.canonical_market_id,
        venue_id=venue.venue_id,
        opportunity_type="prediction_market",
        observed_at=identity.observed_at,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_policy_id=(
            "oracle.validity.prediction_market.int.ola.001"
        ),
        source_record_hash=(
            market_venue_record.record_hash
        ),
        metadata={
            "integration_gate": ENGINE_ID,
        },
    )

    return (
        OracleCanonicalOpportunityValidityExpirationEngine()
        .evaluate(
            request=request,
            evaluated_at=EXPIRED_AT,
            replay_metadata={
                "integration_gate": ENGINE_ID,
                "phase": "expired_validity",
            },
            audit_metadata={
                "request_id": (
                    "audit-int-ola-001-expired"
                ),
            },
        )
    )


def build_comparison_policy():
    return ComparisonScoringPolicy.create(
        policy_id=(
            "oracle.cross_venue.btc_bearish.int.ola.001"
        ),
        component_weights={
            "expected_edge": Decimal("0.35"),
            "liquidity_quality": Decimal("0.20"),
            "thesis_alignment": Decimal("0.25"),
            "time_fit": Decimal("0.10"),
            "venue_quality": Decimal("0.10"),
        },
        higher_score_preferred=True,
    )


def build_kalshi_candidate(
    *,
    market_venue_record,
    validity,
    reference_price,
):
    identity = (
        market_venue_record.canonical_market_identity
    )

    venue = market_venue_record.venue_resolution

    assert venue.venue_id is not None
    assert venue.venue_name is not None
    assert venue.venue_type is not None

    return CrossVenueOpportunityCandidate.create(
        opportunity_id=validity.opportunity_id,
        thesis_id="thesis.btc.bearish.int.ola.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id=identity.canonical_market_id,
        venue_id=venue.venue_id,
        venue_name=venue.venue_name,
        venue_type=venue.venue_type,
        instrument_type=identity.instrument_type,
        opportunity_type="prediction_market",
        expression_type="buy_yes",
        direction="bearish",
        reference_price=reference_price,
        price_unit="USD_PER_SHARE",
        observed_at=validity.observed_at,
        valid_from=validity.valid_from,
        expires_at=validity.expires_at,
        validity_status=validity.validity_status,
        venue_verified=venue.venue_verified,
        source_record_hash=(
            market_venue_record.record_hash
        ),
        validity_evidence_hash=(
            validity.validity_evidence_hash
        ),
        normalized_components={
            "expected_edge": Decimal("0.94"),
            "liquidity_quality": Decimal("0.78"),
            "thesis_alignment": Decimal("0.96"),
            "time_fit": Decimal("0.92"),
            "venue_quality": Decimal("0.88"),
        },
        metadata={
            "source_market_id": identity.source_market_id,
            "source_symbol": identity.source_symbol,
            "share_side": "yes",
        },
    )


def build_coinbase_candidate():
    return CrossVenueOpportunityCandidate.create(
        opportunity_id=(
            "opportunity.coinbase.btc.int.ola.001"
        ),
        thesis_id="thesis.btc.bearish.int.ola.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id=(
            "market.coinbase.btcusd.int.ola.001"
        ),
        venue_id="venue.coinbase",
        venue_name="Coinbase",
        venue_type="crypto_spot",
        instrument_type="spot_asset",
        opportunity_type="crypto_directional",
        expression_type="sell_or_short_thesis",
        direction="bearish",
        reference_price=Decimal("117420"),
        price_unit="USD_PER_BTC",
        observed_at=OBSERVED_AT,
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        validity_status="active",
        venue_verified=True,
        source_record_hash=(
            "record.coinbase.btc.int.ola.001"
        ),
        validity_evidence_hash=(
            "validity.coinbase.btc.int.ola.001"
        ),
        normalized_components={
            "expected_edge": Decimal("0.68"),
            "liquidity_quality": Decimal("0.98"),
            "thesis_alignment": Decimal("0.84"),
            "time_fit": Decimal("0.74"),
            "venue_quality": Decimal("0.93"),
        },
        metadata={
            "asset": "BTC",
            "quote_asset": "USD",
        },
    )


def build_expired_candidate(
    *,
    market_venue_record,
    validity,
):
    identity = (
        market_venue_record.canonical_market_identity
    )

    venue = market_venue_record.venue_resolution

    assert venue.venue_id is not None
    assert venue.venue_name is not None
    assert venue.venue_type is not None

    return CrossVenueOpportunityCandidate.create(
        opportunity_id=validity.opportunity_id,
        thesis_id="thesis.btc.bearish.int.ola.001",
        comparability_group_id=(
            "comparison.btc.bearish.expression"
        ),
        canonical_market_id=identity.canonical_market_id,
        venue_id=venue.venue_id,
        venue_name=venue.venue_name,
        venue_type=venue.venue_type,
        instrument_type=identity.instrument_type,
        opportunity_type="prediction_market",
        expression_type="buy_yes",
        direction="bearish",
        reference_price="0.44",
        price_unit="USD_PER_SHARE",
        observed_at=validity.observed_at,
        valid_from=validity.valid_from,
        expires_at=validity.expires_at,
        validity_status=validity.validity_status,
        venue_verified=venue.venue_verified,
        source_record_hash=(
            market_venue_record.record_hash
        ),
        validity_evidence_hash=(
            validity.validity_evidence_hash
        ),
        normalized_components={
            "expected_edge": Decimal("1.00"),
            "liquidity_quality": Decimal("1.00"),
            "thesis_alignment": Decimal("1.00"),
            "time_fit": Decimal("1.00"),
            "venue_quality": Decimal("1.00"),
        },
        metadata={
            "expired_test_candidate": True,
        },
    )


def run_intelligence_output_path(
    *,
    acquisition_system,
):
    first_observation = get_persisted_observation(
        system=acquisition_system,
        source_market_id="KXBTC-26JUL12-116000",
    )

    second_observation = get_persisted_observation(
        system=acquisition_system,
        source_market_id="KXBTC-26JUL12-117000",
    )

    first_market_venue = build_market_venue_record(
        first_observation
    )

    second_market_venue = build_market_venue_record(
        second_observation
    )

    assert (
        first_market_venue
        .venue_resolution
        .venue_verified
        is True
    )

    assert (
        first_market_venue
        .venue_resolution
        .venue_id
        == "venue.kalshi"
    )

    assert (
        first_market_venue
        .venue_resolution
        .default_venue_used
        is False
    )

    assert (
        first_market_venue
        .venue_resolution
        .fallback_adapter_used
        is False
    )

    assert (
        first_market_venue
        .venue_resolution
        .execution_adapter_resolved
        is False
    )

    active_validity = build_validity_evidence(
        market_venue_record=first_market_venue,
        opportunity_id=(
            "opportunity.kalshi.btc.int.ola.001"
        ),
    )

    expired_validity = build_expired_validity_evidence(
        market_venue_record=second_market_venue,
        opportunity_id=(
            "opportunity.kalshi.btc.expired.int.ola.001"
        ),
    )

    assert active_validity.active is True
    assert active_validity.expired is False

    assert expired_validity.active is False
    assert expired_validity.expired is True

    kalshi_candidate = build_kalshi_candidate(
        market_venue_record=first_market_venue,
        validity=active_validity,
        reference_price="0.31",
    )

    coinbase_candidate = build_coinbase_candidate()

    expired_candidate = build_expired_candidate(
        market_venue_record=second_market_venue,
        validity=expired_validity,
    )

    comparison = (
        OracleCanonicalCrossVenueOpportunityComparisonEngine(
            scoring_policy=build_comparison_policy()
        )
        .compare(
            candidates=(
                kalshi_candidate,
                coinbase_candidate,
                expired_candidate,
            ),
            compared_at=COMPARE_AT,
            replay_metadata={
                "integration_gate": ENGINE_ID,
                "phase": "cross_venue_comparison",
            },
            audit_metadata={
                "request_id": (
                    "audit-int-ola-001-comparison"
                ),
            },
        )
    )

    assert comparison.candidate_count == 3
    assert comparison.eligible_count == 2
    assert comparison.ineligible_count == 1

    assert comparison.best_opportunity_id == (
        "opportunity.kalshi.btc.int.ola.001"
    )

    assert comparison.best_venue_id == "venue.kalshi"
    assert comparison.best_venue_name == "Kalshi"

    assert comparison.best_expression_type == "buy_yes"
    assert comparison.best_direction == "bearish"

    assert comparison.best_reference_price == "0.31"
    assert comparison.best_price_unit == "USD_PER_SHARE"

    assert comparison.tie_for_best is False

    assert comparison.comparison_status == (
        "best_opportunity_resolved"
    )

    assert (
        "raw_prices_not_compared_directly"
        in comparison.reason_codes
    )

    alert = (
        OracleCanonicalOpportunityAlertRecordEngine()
        .create_alert(
            comparison=comparison,
            alert_created_at=ALERT_CREATED_AT,
            display_metadata={
                "display_timezone": "America/Chicago",
                "display_timezone_label": "CT",
                "date_required": True,
                "time_required": True,
                "expiration_required": True,
                "venue_next_to_price_required": True,
            },
            replay_metadata={
                "integration_gate": ENGINE_ID,
                "phase": "canonical_alert",
            },
            audit_metadata={
                "request_id": (
                    "audit-int-ola-001-alert"
                ),
            },
        )
    )

    assert alert.alert_status == "active"
    assert alert.freshness_status == "fresh"

    assert alert.venue_id == "venue.kalshi"
    assert alert.venue_name == "Kalshi"

    assert alert.reference_price == "0.31"
    assert alert.price_unit == "USD_PER_SHARE"

    assert alert.expression_type == "buy_yes"
    assert alert.direction == "bearish"

    assert alert.source_expires_at == EXPIRES_AT

    assert alert.alert_date_utc == "2026-07-12"
    assert alert.expiration_date_utc == "2026-07-12"

    return {
        "first_observation": first_observation,
        "second_observation": second_observation,
        "first_market_venue": first_market_venue,
        "second_market_venue": second_market_venue,
        "active_validity": active_validity,
        "expired_validity": expired_validity,
        "comparison": comparison,
        "alert": alert,
    }


def assert_permanent_no_execution_invariants(
    *,
    decision,
    cycle,
    intelligence,
):
    first_market_venue = intelligence[
        "first_market_venue"
    ]

    active_validity = intelligence[
        "active_validity"
    ]

    comparison = intelligence["comparison"]

    alert = intelligence["alert"]

    assert decision.read_only is True
    assert decision.execution_allowed is False

    assert (
        decision.trade_authorization_allowed
        is False
    )

    assert decision.order_placement_allowed is False

    assert (
        decision.execution_adapter_invocation_allowed
        is False
    )

    assert decision.funds_moved is False
    assert decision.portfolio_mutated is False

    assert cycle.read_only is True
    assert cycle.execution_allowed is False
    assert cycle.execution_adapter_resolved is False
    assert cycle.execution_adapter_invoked is False

    assert (
        cycle.trade_authorization_allowed
        is False
    )

    assert cycle.order_placement_allowed is False
    assert cycle.funds_moved is False
    assert cycle.portfolio_mutated is False

    assert first_market_venue.read_only is True

    assert (
        first_market_venue.execution_allowed
        is False
    )

    assert (
        first_market_venue
        .trade_authorization_allowed
        is False
    )

    assert (
        first_market_venue
        .order_placement_allowed
        is False
    )

    assert (
        first_market_venue
        .execution_adapter_invocation_allowed
        is False
    )

    assert first_market_venue.funds_moved is False

    assert (
        first_market_venue.portfolio_mutated
        is False
    )

    assert active_validity.read_only is True
    assert active_validity.execution_allowed is False

    assert (
        active_validity.trade_authorization_allowed
        is False
    )

    assert (
        active_validity.order_placement_allowed
        is False
    )

    assert (
        active_validity
        .execution_adapter_invocation_allowed
        is False
    )

    assert active_validity.funds_moved is False
    assert active_validity.portfolio_mutated is False

    assert comparison.read_only is True
    assert comparison.execution_allowed is False
    assert comparison.execution_adapter_resolved is False
    assert comparison.execution_adapter_invoked is False

    assert (
        comparison.trade_authorization_allowed
        is False
    )

    assert comparison.order_placement_allowed is False
    assert comparison.funds_moved is False
    assert comparison.portfolio_mutated is False

    assert alert.read_only is True
    assert alert.execution_allowed is False
    assert alert.execution_adapter_resolved is False
    assert alert.execution_adapter_invoked is False

    assert (
        alert.trade_authorization_allowed
        is False
    )

    assert alert.order_placement_allowed is False
    assert alert.funds_moved is False
    assert alert.portfolio_mutated is False


def run_full_subsystem_gate():
    (
        acquisition_system,
        source_control_decision,
        cycle,
    ) = run_controlled_acquisition_path()

    (
        blocked_system,
        blocked_decision,
        blocked_cycle,
    ) = run_blocked_source_control_path()

    intelligence = run_intelligence_output_path(
        acquisition_system=acquisition_system
    )

    assert_permanent_no_execution_invariants(
        decision=source_control_decision,
        cycle=cycle,
        intelligence=intelligence,
    )

    assert blocked_decision.acquisition_allowed is False
    assert blocked_cycle.acquisition_invoked is False

    assert (
        blocked_system["adapter"].acquire_call_count
        == 0
    )

    persistence_snapshot = (
        acquisition_system["persistence_ledger"]
        .export_snapshot(
            snapshot_at=ALERT_CREATED_AT,
            replay_metadata={
                "integration_gate": ENGINE_ID,
                "phase": "persistence_snapshot",
            },
            audit_metadata={
                "request_id": (
                    "audit-int-ola-001-persistence-snapshot"
                ),
            },
        )
    )

    assert persistence_snapshot.entry_count == 2

    restored_persistence = (
        OracleCanonicalObservationPersistenceLedger
        .restore_snapshot(
            snapshot=persistence_snapshot
        )
    )

    assert restored_persistence.entry_count == 2

    assert (
        restored_persistence.terminal_chain_hash
        == acquisition_system[
            "persistence_ledger"
        ].terminal_chain_hash
    )

    return {
        "acquisition_system": acquisition_system,
        "source_control_decision": (
            source_control_decision
        ),
        "cycle": cycle,
        "blocked_cycle": blocked_cycle,
        "intelligence": intelligence,
        "persistence_snapshot": persistence_snapshot,
        "restored_persistence": restored_persistence,
    }


def run_deterministic_replay_gate():
    first = run_full_subsystem_gate()
    second = run_full_subsystem_gate()

    assert (
        first["source_control_decision"].decision_hash
        == second["source_control_decision"].decision_hash
    )

    assert (
        first["cycle"].cycle_hash
        == second["cycle"].cycle_hash
    )

    assert (
        first["cycle"].persistence_terminal_chain_hash
        == second["cycle"].persistence_terminal_chain_hash
    )

    assert (
        first["intelligence"]["first_market_venue"]
        .record_hash
        == second["intelligence"]["first_market_venue"]
        .record_hash
    )

    assert (
        first["intelligence"]["active_validity"]
        .validity_evidence_hash
        == second["intelligence"]["active_validity"]
        .validity_evidence_hash
    )

    assert (
        first["intelligence"]["comparison"]
        .comparison_hash
        == second["intelligence"]["comparison"]
        .comparison_hash
    )

    assert (
        first["intelligence"]["alert"].alert_hash
        == second["intelligence"]["alert"].alert_hash
    )

    assert (
        first["persistence_snapshot"].snapshot_hash
        == second["persistence_snapshot"].snapshot_hash
    )

    return first


def main():
    result = run_deterministic_replay_gate()

    system = result["acquisition_system"]

    decision = result["source_control_decision"]

    cycle = result["cycle"]

    blocked_cycle = result["blocked_cycle"]

    intelligence = result["intelligence"]

    market_venue = intelligence[
        "first_market_venue"
    ]

    active_validity = intelligence[
        "active_validity"
    ]

    expired_validity = intelligence[
        "expired_validity"
    ]

    comparison = intelligence["comparison"]

    alert = intelligence["alert"]

    persistence_snapshot = result[
        "persistence_snapshot"
    ]

    output = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "ola_001_acquisition_runtime_passed": True,
        "ola_002_source_control_passed": True,
        "ola_003_deduplication_passed": True,
        "ola_004_market_identity_venue_passed": True,
        "ola_005_validity_expiration_passed": True,
        "ola_006_cross_venue_comparison_passed": True,
        "ola_007_alert_record_passed": True,
        "ola_008_persistence_ledger_passed": True,
        "ola_009_persistence_router_passed": True,
        "ola_010_cycle_orchestrator_passed": True,
        "source_control_acquisition_allowed": (
            decision.acquisition_allowed
        ),
        "blocked_cycle_acquisition_invoked": (
            blocked_cycle.acquisition_invoked
        ),
        "observation_count": cycle.observation_count,
        "canonical_count": cycle.canonical_count,
        "duplicate_count": cycle.duplicate_count,
        "routed_count": cycle.routed_count,
        "persisted_count": cycle.persisted_count,
        "persistence_entry_count": (
            system["persistence_ledger"].entry_count
        ),
        "persistence_chain_valid": (
            cycle.persistence_terminal_chain_hash
            == system["persistence_ledger"]
            .terminal_chain_hash
        ),
        "persistence_snapshot_entry_count": (
            persistence_snapshot.entry_count
        ),
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
        "active_validity_status": (
            active_validity.validity_status
        ),
        "expired_validity_status": (
            expired_validity.validity_status
        ),
        "comparison_status": (
            comparison.comparison_status
        ),
        "best_venue_id": comparison.best_venue_id,
        "best_venue_name": comparison.best_venue_name,
        "best_expression_type": (
            comparison.best_expression_type
        ),
        "best_direction": comparison.best_direction,
        "best_reference_price": (
            comparison.best_reference_price
        ),
        "best_price_unit": (
            comparison.best_price_unit
        ),
        "raw_prices_compared_directly": False,
        "normalized_scoring_used": True,
        "alert_status": alert.alert_status,
        "alert_venue_id": alert.venue_id,
        "alert_venue_name": alert.venue_name,
        "alert_reference_price": (
            alert.reference_price
        ),
        "alert_price_unit": alert.price_unit,
        "alert_direction": alert.direction,
        "alert_expression_type": (
            alert.expression_type
        ),
        "explicit_alert_date_time": True,
        "explicit_expiration": True,
        "deterministic_replay_passed": True,
        "read_only": True,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    print(
        "[PASS] INT-OLA-001 Oracle Live Acquisition "
        "Full Subsystem Integration Gate"
    )

    print(output)


if __name__ == "__main__":
    main()
