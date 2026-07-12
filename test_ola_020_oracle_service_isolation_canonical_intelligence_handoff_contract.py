from dataclasses import FrozenInstanceError
from datetime import datetime, timezone


from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    CanonicalIntelligenceHandoffContractError,
    CanonicalIntelligenceHandoffRecord,
    OracleQSeriesServiceIsolationContract,
    OracleServiceIsolationContractError,
)


VALID_FROM = datetime(
    2026,
    7,
    12,
    15,
    0,
    0,
    tzinfo=timezone.utc,
)

INTELLIGENCE_GENERATED_AT = datetime(
    2026,
    7,
    12,
    15,
    0,
    2,
    tzinfo=timezone.utc,
)

PUBLISHED_AT = datetime(
    2026,
    7,
    12,
    15,
    0,
    5,
    tzinfo=timezone.utc,
)

EXPIRES_AT = datetime(
    2026,
    7,
    12,
    15,
    15,
    0,
    tzinfo=timezone.utc,
)


def build_service_contract():
    return OracleQSeriesServiceIsolationContract.create(
        contract_id=(
            "oracle.qseries.service_isolation.v1"
        ),
        oracle_service_id=(
            "service.oracle.intelligence"
        ),
        qseries_service_id=(
            "service.qseries.execution"
        ),
        contract_metadata={
            "environment": "production",
            "handoff_transport": "durable_boundary",
            "oracle_process": "separate",
            "qseries_process": "separate",
        },
    )


def build_handoff():
    return CanonicalIntelligenceHandoffRecord.create(
        service_contract=build_service_contract(),
        opportunity_id=(
            "opportunity.kalshi.btc.ola020.001"
        ),
        thesis_id=(
            "thesis.btc.bearish.ola020.001"
        ),
        canonical_market_id=(
            "market."
            "95b13d7489267bf051b0173a27c3e98b"
            "155473362c6ca4e47431a16e623044ab"
        ),
        source_market_id=(
            "KXBTC-26JUL12-116000"
        ),
        venue_id="venue.kalshi",
        venue_name="Kalshi",
        venue_type="prediction_market",
        venue_verified=True,
        opportunity_type="prediction_market",
        instrument_type="prediction_contract",
        expression_type="buy_yes",
        direction="bearish",
        reference_price="0.31",
        price_unit="USD_PER_SHARE",
        valid_from=VALID_FROM,
        expires_at=EXPIRES_AT,
        intelligence_generated_at=(
            INTELLIGENCE_GENERATED_AT
        ),
        published_at=PUBLISHED_AT,
        oracle_evidence_hash=(
            "a" * 64
        ),
        replay_reference_id=(
            "replay.oracle.ola020.001"
        ),
        replay_evidence_hash=(
            "b" * 64
        ),
        source_record_id=(
            "observation.kalshi.ola020.001"
        ),
        source_record_hash=(
            "c" * 64
        ),
        handoff_metadata={
            "publisher": "oracle",
            "consumer": "qseries",
            "historical_oi_handoff_replaced": False,
            "modern_canonical_boundary": True,
        },
    )


def run_service_isolation_contract_test():
    contract = build_service_contract()

    assert contract.schema_version == "OLA-020"

    assert contract.engine_id == "OLA-020"

    assert contract.contract_id == (
        "oracle.qseries.service_isolation.v1"
    )

    assert contract.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert contract.oracle_service_role == (
        "oracle_read_only_intelligence"
    )

    assert contract.qseries_service_id == (
        "service.qseries.execution"
    )

    assert contract.qseries_service_role == (
        "qseries_authorization_execution"
    )

    assert contract.separate_process_required is True

    assert (
        contract.direct_execution_import_allowed
        is False
    )

    assert contract.oracle_execution_authority is False

    assert (
        contract.qseries_oracle_history_mutation_allowed
        is False
    )

    assert contract.immutable_handoff_required is True

    assert (
        contract.durable_handoff_boundary_required
        is True
    )

    assert (
        contract.independent_qseries_validation_required
        is True
    )

    assert len(contract.contract_hash) == 64

    assert contract.immutable is True
    assert contract.replayable is True
    assert contract.auditable is True
    assert contract.explainable is True
    assert contract.read_only is True

    assert contract.execution_allowed is False

    assert contract.execution_adapter_resolved is False

    assert contract.execution_adapter_invoked is False

    assert contract.trade_authorization_allowed is False

    assert contract.order_placement_allowed is False

    assert contract.funds_moved is False

    assert contract.portfolio_mutated is False

    try:
        contract.oracle_execution_authority = True

        raise AssertionError(
            "service contract must be immutable"
        )

    except FrozenInstanceError:
        pass

    return contract


def run_canonical_handoff_test():
    handoff = build_handoff()

    assert handoff.schema_version == "OLA-020"

    assert handoff.engine_id == "OLA-020"

    assert handoff.handoff_id.startswith(
        "handoff."
    )

    assert handoff.handoff_status == "published"

    assert handoff.service_contract_id == (
        "oracle.qseries.service_isolation.v1"
    )

    assert len(handoff.service_contract_hash) == 64

    assert handoff.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert handoff.qseries_service_id == (
        "service.qseries.execution"
    )

    assert handoff.opportunity_id == (
        "opportunity.kalshi.btc.ola020.001"
    )

    assert handoff.thesis_id == (
        "thesis.btc.bearish.ola020.001"
    )

    assert handoff.canonical_market_id.startswith(
        "market."
    )

    assert handoff.source_market_id == (
        "KXBTC-26JUL12-116000"
    )

    assert handoff.venue_id == "venue.kalshi"

    assert handoff.venue_name == "Kalshi"

    assert handoff.venue_type == "prediction_market"

    assert handoff.venue_verified is True

    assert handoff.opportunity_type == (
        "prediction_market"
    )

    assert handoff.instrument_type == (
        "prediction_contract"
    )

    assert handoff.expression_type == "buy_yes"

    assert handoff.direction == "bearish"

    assert handoff.reference_price == "0.31"

    assert handoff.price_unit == "USD_PER_SHARE"

    assert handoff.valid_from == VALID_FROM

    assert handoff.expires_at == EXPIRES_AT

    assert (
        handoff.intelligence_generated_at
        == INTELLIGENCE_GENERATED_AT
    )

    assert handoff.published_at == PUBLISHED_AT

    assert len(handoff.oracle_evidence_hash) == 64

    assert handoff.replay_reference_id == (
        "replay.oracle.ola020.001"
    )

    assert len(handoff.replay_evidence_hash) == 64

    assert handoff.source_record_id == (
        "observation.kalshi.ola020.001"
    )

    assert len(handoff.source_record_hash) == 64

    assert (
        handoff.independent_qseries_validation_required
        is True
    )

    assert handoff.execution_adapter_resolved is False

    assert handoff.execution_adapter_invoked is False

    assert handoff.trade_authorization_allowed is False

    assert handoff.order_placement_allowed is False

    assert handoff.funds_moved is False

    assert handoff.portfolio_mutated is False

    assert handoff.immutable is True
    assert handoff.replayable is True
    assert handoff.auditable is True
    assert handoff.explainable is True
    assert handoff.read_only is True

    assert handoff.execution_allowed is False

    assert len(handoff.handoff_hash) == 64

    assert handoff.verify_handoff_hash() is True

    try:
        handoff.reference_price = "0.99"

        raise AssertionError(
            "handoff record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return handoff


def run_deterministic_replay_test():
    first = build_handoff()

    second = build_handoff()

    assert first == second

    assert first.handoff_id == second.handoff_id

    assert first.handoff_hash == second.handoff_hash

    assert first.verify_handoff_hash() is True

    assert second.verify_handoff_hash() is True


def run_fail_closed_tests():
    try:
        OracleQSeriesServiceIsolationContract.create(
            contract_id="invalid.same.service",
            oracle_service_id="service.shared",
            qseries_service_id="service.shared",
            contract_metadata={},
        )

        raise AssertionError(
            "shared Oracle/Q Series service identity "
            "must fail closed"
        )

    except OracleServiceIsolationContractError:
        pass

    base = {
        "service_contract": build_service_contract(),
        "opportunity_id": "opportunity.test",
        "thesis_id": "thesis.test",
        "canonical_market_id": "market.test",
        "source_market_id": "source-market-test",
        "venue_id": "venue.kalshi",
        "venue_name": "Kalshi",
        "venue_type": "prediction_market",
        "venue_verified": True,
        "opportunity_type": "prediction_market",
        "instrument_type": "prediction_contract",
        "expression_type": "buy_yes",
        "direction": "bearish",
        "reference_price": "0.31",
        "price_unit": "USD_PER_SHARE",
        "valid_from": VALID_FROM,
        "expires_at": EXPIRES_AT,
        "intelligence_generated_at": (
            INTELLIGENCE_GENERATED_AT
        ),
        "published_at": PUBLISHED_AT,
        "oracle_evidence_hash": "a" * 64,
        "replay_reference_id": "replay.test",
        "replay_evidence_hash": "b" * 64,
        "source_record_id": "observation.test",
        "source_record_hash": "c" * 64,
        "handoff_metadata": {},
    }

    invalid_venue = dict(base)

    invalid_venue["venue_verified"] = False

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **invalid_venue
        )

        raise AssertionError(
            "unverified venue must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass

    expired = dict(base)

    expired["published_at"] = EXPIRES_AT

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **expired
        )

        raise AssertionError(
            "expired handoff must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass

    naive_time = dict(base)

    naive_time["valid_from"] = datetime(
        2026,
        7,
        12,
        15,
        0,
        0,
    )

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **naive_time
        )

        raise AssertionError(
            "naive contract timestamp must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass

    invalid_hash = dict(base)

    invalid_hash["oracle_evidence_hash"] = "not-a-hash"

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **invalid_hash
        )

        raise AssertionError(
            "invalid evidence hash must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass

    secret_metadata = dict(base)

    secret_metadata["handoff_metadata"] = {
        "api_key": "must-not-enter-handoff"
    }

    try:
        CanonicalIntelligenceHandoffRecord.create(
            **secret_metadata
        )

        raise AssertionError(
            "secret-bearing metadata must fail closed"
        )

    except CanonicalIntelligenceHandoffContractError:
        pass


def main():
    contract = run_service_isolation_contract_test()

    handoff = run_canonical_handoff_test()

    run_deterministic_replay_test()

    run_fail_closed_tests()

    result = {
        "schema_version": handoff.schema_version,
        "engine_id": handoff.engine_id,
        "status": "passed",
        "contract_id": contract.contract_id,
        "oracle_service_id": (
            contract.oracle_service_id
        ),
        "oracle_service_role": (
            contract.oracle_service_role
        ),
        "qseries_service_id": (
            contract.qseries_service_id
        ),
        "qseries_service_role": (
            contract.qseries_service_role
        ),
        "separate_process_required": (
            contract.separate_process_required
        ),
        "direct_execution_import_allowed": (
            contract.direct_execution_import_allowed
        ),
        "oracle_execution_authority": (
            contract.oracle_execution_authority
        ),
        "qseries_oracle_history_mutation_allowed": (
            contract.qseries_oracle_history_mutation_allowed
        ),
        "immutable_handoff_required": (
            contract.immutable_handoff_required
        ),
        "durable_handoff_boundary_required": (
            contract.durable_handoff_boundary_required
        ),
        "independent_qseries_validation_required": (
            handoff.independent_qseries_validation_required
        ),
        "handoff_status": handoff.handoff_status,
        "canonical_market_id": (
            handoff.canonical_market_id
        ),
        "source_market_id": handoff.source_market_id,
        "venue_id": handoff.venue_id,
        "venue_name": handoff.venue_name,
        "venue_verified": handoff.venue_verified,
        "opportunity_type": handoff.opportunity_type,
        "instrument_type": handoff.instrument_type,
        "expression_type": handoff.expression_type,
        "direction": handoff.direction,
        "reference_price": handoff.reference_price,
        "price_unit": handoff.price_unit,
        "explicit_valid_from": (
            handoff.valid_from.isoformat()
        ),
        "explicit_expires_at": (
            handoff.expires_at.isoformat()
        ),
        "oracle_evidence_hash_preserved": True,
        "replay_reference_preserved": True,
        "source_record_identity_preserved": True,
        "deterministic_handoff_hashing": True,
        "unverified_venue_blocked": True,
        "expired_handoff_blocked": True,
        "naive_timestamp_blocked": True,
        "invalid_evidence_hash_blocked": True,
        "secret_metadata_blocked": True,
        "execution_adapter_resolved": (
            handoff.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            handoff.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            handoff.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            handoff.order_placement_allowed
        ),
        "funds_moved": handoff.funds_moved,
        "portfolio_mutated": handoff.portfolio_mutated,
        "read_only": handoff.read_only,
        "execution_allowed": handoff.execution_allowed,
    }

    print(
        "[PASS] OLA-020 Oracle Service Isolation and "
        "Canonical Intelligence Handoff Contract"
    )

    print(result)


if __name__ == "__main__":
    main()
