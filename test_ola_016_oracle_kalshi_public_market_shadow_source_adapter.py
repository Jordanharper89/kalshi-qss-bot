from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json
from urllib.parse import parse_qs, urlparse


from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
    ADAPTER_ID,
    PRODUCTION_BASE_URL,
    SOURCE_ID,
    OracleKalshiPublicMarketShadowSourceAdapter,
    KalshiShadowAdapterContractError,
    KalshiShadowAdapterSourceError,
    raw_observation_canonical_dict,
    raw_observation_stable_hash,
)


CHECKED_AT = datetime(
    2026,
    7,
    12,
    8,
    0,
    0,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    8,
    0,
    1,
    tzinfo=timezone.utc,
)


def market(
    *,
    ticker,
    event_ticker,
    updated_time,
    title,
    yes_bid,
    yes_ask,
    last_price,
    volume,
    liquidity,
):
    return {
        "ticker": ticker,
        "event_ticker": event_ticker,
        "yes_sub_title": "Yes",
        "no_sub_title": "No",
        "created_time": "2026-07-12T07:50:00Z",
        "updated_time": updated_time,
        "open_time": "2026-07-12T07:55:00Z",
        "close_time": "2026-07-12T22:00:00Z",
        "latest_expiration_time": (
            "2026-07-12T22:05:00Z"
        ),
        "settlement_timer_seconds": 60,
        "yes_bid_dollars": yes_bid,
        "yes_bid_size_fp": "25.00",
        "yes_ask_dollars": yes_ask,
        "yes_ask_size_fp": "30.00",
        "no_bid_dollars": "0.6800",
        "no_ask_dollars": "0.7000",
        "last_price_dollars": last_price,
        "volume_fp": volume,
        "volume_24h_fp": volume,
        "can_close_early": False,
        "open_interest_fp": "420.00",
        "notional_value_dollars": "1.0000",
        "previous_yes_bid_dollars": "0.2900",
        "previous_yes_ask_dollars": "0.3200",
        "previous_price_dollars": "0.3000",
        "expiration_value": "",
        "rules_primary": "Test market rules",
        "rules_secondary": "",
        "price_level_structure": "linear_cent",
        "price_ranges": [],
        "title": title,
        "subtitle": "Shadow acquisition test",
        "expected_expiration_time": (
            "2026-07-12T22:00:00Z"
        ),
        "expiration_time": "2026-07-12T22:00:00Z",
        "liquidity_dollars": liquidity,
        "settlement_value_dollars": None,
        "settlement_ts": None,
        "occurrence_datetime": (
            "2026-07-12T21:00:00Z"
        ),
        "fee_waiver_expiration_time": None,
        "early_close_condition": "",
        "floor_strike": 116000,
        "cap_strike": None,
        "functional_strike": "116000",
        "custom_strike": {},
        "mve_collection_ticker": None,
        "mve_selected_legs": [],
        "primary_participant_key": None,
        "is_provisional": False,
        "exchange_index": 1,
    }


FIRST_MARKET = market(
    ticker="KXBTC-26JUL12-116000",
    event_ticker="KXBTC-26JUL12",
    updated_time="2026-07-12T07:59:58Z",
    title="Bitcoin below 116000 by 5 PM",
    yes_bid="0.3000",
    yes_ask="0.3200",
    last_price="0.3100",
    volume="1250.00",
    liquidity="5400.00",
)


SECOND_MARKET = market(
    ticker="KXBTC-26JUL12-117000",
    event_ticker="KXBTC-26JUL12",
    updated_time="2026-07-12T07:59:59Z",
    title="Bitcoin below 117000 by 5 PM",
    yes_bid="0.4300",
    yes_ask="0.4500",
    last_price="0.4400",
    volume="1800.00",
    liquidity="7100.00",
)


class DeterministicFetcher:
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
        self.calls.append(
            {
                "url": url,
                "timeout_seconds": timeout_seconds,
            }
        )

        query = parse_qs(
            urlparse(url).query
        )

        cursor = query.get(
            "cursor",
            [None],
        )[0]

        if cursor is None:
            return (
                200,
                json.dumps(
                    {
                        "markets": [
                            FIRST_MARKET,
                        ],
                        "cursor": "cursor.page.2",
                    }
                ),
            )

        if cursor == "cursor.page.2":
            return (
                200,
                json.dumps(
                    {
                        "markets": [
                            SECOND_MARKET,
                        ],
                        "cursor": "",
                    }
                ),
            )

        raise AssertionError(
            "unexpected cursor"
        )


def build_adapter():
    fetcher = DeterministicFetcher()

    adapter = (
        OracleKalshiPublicMarketShadowSourceAdapter(
            market_status="open",
            page_limit=1000,
            max_pages=2,
            timeout_seconds=20,
            base_url=PRODUCTION_BASE_URL,
            http_fetcher=fetcher,
        )
    )

    return adapter, fetcher


def run_health_test():
    adapter, fetcher = build_adapter()

    health = adapter.probe_health(
        checked_at=CHECKED_AT
    )

    assert health.schema_version == "OLA-016"
    assert health.engine_id == "OLA-016"

    assert health.adapter_id == ADAPTER_ID
    assert health.source_id == SOURCE_ID

    assert health.reachable is True

    assert health.public_endpoint is True
    assert health.authentication_used is False

    assert health.http_method == "GET"
    assert health.endpoint_path == "/markets"

    assert health.shadow_mode is True
    assert health.alerts_allowed is False

    assert health.qseries_intake_allowed is False

    assert health.health_status == "healthy"

    assert health.read_only is True
    assert health.execution_allowed is False

    assert (
        health.trade_authorization_allowed
        is False
    )

    assert health.order_placement_allowed is False

    assert (
        health.execution_adapter_invocation_allowed
        is False
    )

    assert health.funds_moved is False
    assert health.portfolio_mutated is False

    assert len(fetcher.calls) == 1

    return health


def run_acquisition_test():
    adapter, fetcher = build_adapter()

    observations = adapter.acquire(
        acquired_at=ACQUIRED_AT
    )

    assert len(observations) == 2

    assert len(fetcher.calls) == 2

    first_url = fetcher.calls[0]["url"]
    second_url = fetcher.calls[1]["url"]

    first_query = parse_qs(
        urlparse(first_url).query
    )

    second_query = parse_qs(
        urlparse(second_url).query
    )

    assert first_query["status"] == ["open"]
    assert first_query["limit"] == ["1000"]

    assert "cursor" not in first_query

    assert second_query["cursor"] == [
        "cursor.page.2"
    ]

    first = observations[0]
    second = observations[1]

    assert first.observation_type == "market_snapshot"

    first_payload = dict(
        first.payload
    )

    second_payload = dict(
        second.payload
    )

    assert first_payload["source_market_id"] == (
        "KXBTC-26JUL12-116000"
    )

    assert first_payload["source_symbol"] == (
        "KXBTC-26JUL12-116000"
    )

    assert first_payload["event_ticker"] == (
        "KXBTC-26JUL12"
    )

    assert first_payload["instrument_type"] == (
        "prediction_contract"
    )

    assert first_payload["venue_claim"] == (
        "venue.kalshi"
    )

    assert first_payload["yes_bid_dollars"] == (
        "0.3000"
    )

    assert first_payload["yes_ask_dollars"] == (
        "0.3200"
    )

    assert first_payload["last_price_dollars"] == (
        "0.3100"
    )

    assert first_payload["volume_fp"] == (
        "1250.00"
    )

    assert first_payload["liquidity_dollars"] == (
        "5400.00"
    )

    assert first_payload["source_expiration_time"] == (
        "2026-07-12T22:00:00Z"
    )

    assert first_payload[
        "source_occurrence_datetime"
    ] == "2026-07-12T21:00:00Z"

    assert first_payload["shadow_mode"] is True

    assert first_payload["alerts_allowed"] is False

    assert (
        first_payload["qseries_intake_allowed"]
        is False
    )

    assert first.observed_at == datetime(
        2026,
        7,
        12,
        7,
        59,
        58,
        tzinfo=timezone.utc,
    )

    first_provenance = dict(
        first.provenance
    )

    assert first_provenance["source_id"] == SOURCE_ID

    assert first_provenance["adapter_id"] == ADAPTER_ID

    assert first_provenance["venue_id"] == (
        "venue.kalshi"
    )

    assert first_provenance["source_environment"] == (
        "production"
    )

    assert first_provenance["source_endpoint"] == (
        "/markets"
    )

    assert first_provenance["http_method"] == "GET"

    assert first_provenance["public_endpoint"] is True

    assert (
        first_provenance["authentication_used"]
        is False
    )

    assert first_provenance["shadow_mode"] is True

    assert second_payload["source_market_id"] == (
        "KXBTC-26JUL12-117000"
    )

    first_raw_dict = raw_observation_canonical_dict(
        first
    )

    assert first_raw_dict == {
        "source_observation_id": (
            first.source_observation_id
        ),
        "observed_at": first.observed_at.isoformat(),
        "observation_type": first.observation_type,
        "payload": dict(first.payload),
        "provenance": dict(first.provenance),
    }

    first_raw_hash = raw_observation_stable_hash(
        first
    )

    second_raw_hash = raw_observation_stable_hash(
        second
    )

    assert isinstance(first_raw_hash, str)
    assert len(first_raw_hash) == 64

    assert isinstance(second_raw_hash, str)
    assert len(second_raw_hash) == 64

    assert first_raw_hash != second_raw_hash

    evidence = adapter.last_acquisition_evidence

    assert evidence is not None

    assert evidence.schema_version == "OLA-016"

    assert evidence.engine_id == "OLA-016"

    assert evidence.market_status_filter == "open"

    assert evidence.page_limit == 1000

    assert evidence.max_pages == 2

    assert evidence.pages_requested == 2

    assert evidence.source_market_count == 2

    assert evidence.observation_count == 2

    assert evidence.raw_observation_hashes == (
        first_raw_hash,
        second_raw_hash,
    )

    assert evidence.terminal_cursor_present is False

    assert evidence.shadow_mode is True

    assert evidence.alerts_allowed is False

    assert evidence.qseries_intake_allowed is False

    assert evidence.canonical_replay_hash_created is False

    assert evidence.read_only is True

    assert evidence.execution_allowed is False

    assert (
        evidence.trade_authorization_allowed
        is False
    )

    assert evidence.order_placement_allowed is False

    assert (
        evidence.execution_adapter_invocation_allowed
        is False
    )

    assert evidence.funds_moved is False

    assert evidence.portfolio_mutated is False

    try:
        evidence.shadow_mode = False

        raise AssertionError(
            "acquisition evidence must be immutable"
        )

    except FrozenInstanceError:
        pass

    return adapter, observations, evidence


def run_deterministic_replay_test():
    first_adapter, first_fetcher = build_adapter()

    second_adapter, second_fetcher = build_adapter()

    first = first_adapter.acquire(
        acquired_at=ACQUIRED_AT
    )

    second = second_adapter.acquire(
        acquired_at=ACQUIRED_AT
    )

    assert first == second

    assert (
        first_adapter.last_acquisition_evidence
        == second_adapter.last_acquisition_evidence
    )

    first_raw_hashes = tuple(
        raw_observation_stable_hash(
            observation
        )
        for observation in first
    )

    second_raw_hashes = tuple(
        raw_observation_stable_hash(
            observation
        )
        for observation in second
    )

    assert first_raw_hashes == second_raw_hashes

    assert (
        first_adapter
        .last_acquisition_evidence
        .raw_observation_hashes
        == first_raw_hashes
    )

    return first


def run_non_200_fail_closed_test():
    def fetcher(
        *,
        url,
        timeout_seconds,
    ):
        return 503, '{"error":"unavailable"}'

    adapter = (
        OracleKalshiPublicMarketShadowSourceAdapter(
            http_fetcher=fetcher
        )
    )

    try:
        adapter.acquire(
            acquired_at=ACQUIRED_AT
        )

        raise AssertionError(
            "non-200 response must fail closed"
        )

    except KalshiShadowAdapterSourceError:
        pass

    assert adapter.last_acquisition_evidence is None


def run_invalid_json_fail_closed_test():
    def fetcher(
        *,
        url,
        timeout_seconds,
    ):
        return 200, "not-json"

    adapter = (
        OracleKalshiPublicMarketShadowSourceAdapter(
            http_fetcher=fetcher
        )
    )

    try:
        adapter.acquire(
            acquired_at=ACQUIRED_AT
        )

        raise AssertionError(
            "invalid JSON must fail closed"
        )

    except KalshiShadowAdapterSourceError:
        pass


def run_malformed_market_fail_closed_test():
    def fetcher(
        *,
        url,
        timeout_seconds,
    ):
        return (
            200,
            json.dumps(
                {
                    "markets": [
                        {
                            "ticker": "",
                            "event_ticker": "TEST",
                            "title": "Malformed market",
                            "updated_time": (
                                "2026-07-12T07:59:58Z"
                            ),
                        }
                    ],
                    "cursor": "",
                }
            ),
        )

    adapter = (
        OracleKalshiPublicMarketShadowSourceAdapter(
            http_fetcher=fetcher
        )
    )

    try:
        adapter.acquire(
            acquired_at=ACQUIRED_AT
        )

        raise AssertionError(
            "malformed market must fail closed"
        )

    except KalshiShadowAdapterContractError:
        pass


def run_configuration_fail_closed_tests():
    try:
        OracleKalshiPublicMarketShadowSourceAdapter(
            market_status="invalid"
        )

        raise AssertionError(
            "invalid status must fail closed"
        )

    except KalshiShadowAdapterContractError:
        pass

    try:
        OracleKalshiPublicMarketShadowSourceAdapter(
            page_limit=1001
        )

        raise AssertionError(
            "page limit above 1000 must fail closed"
        )

    except KalshiShadowAdapterContractError:
        pass

    try:
        OracleKalshiPublicMarketShadowSourceAdapter(
            max_pages=0
        )

        raise AssertionError(
            "zero max_pages must fail closed"
        )

    except KalshiShadowAdapterContractError:
        pass


def run_timestamp_fail_closed_test():
    adapter, fetcher = build_adapter()

    try:
        adapter.acquire(
            acquired_at=datetime(
                2026,
                7,
                12,
                8,
                0,
                1,
            )
        )

        raise AssertionError(
            "naive acquired_at must fail closed"
        )

    except KalshiShadowAdapterContractError:
        pass

    assert len(fetcher.calls) == 0


def main():
    health = run_health_test()

    (
        adapter,
        observations,
        evidence,
    ) = run_acquisition_test()

    replay_observations = (
        run_deterministic_replay_test()
    )

    run_non_200_fail_closed_test()

    run_invalid_json_fail_closed_test()

    run_malformed_market_fail_closed_test()

    run_configuration_fail_closed_tests()

    run_timestamp_fail_closed_test()

    result = {
        "schema_version": evidence.schema_version,
        "engine_id": evidence.engine_id,
        "status": "passed",
        "adapter_id": adapter.adapter_id,
        "source_id": adapter.source_id,
        "source_environment": "production",
        "source_endpoint": "/markets",
        "http_method": "GET",
        "public_endpoint": True,
        "authentication_used": False,
        "market_status_filter": (
            evidence.market_status_filter
        ),
        "page_limit": evidence.page_limit,
        "pages_requested": evidence.pages_requested,
        "observation_count": evidence.observation_count,
        "raw_observation_hash_count": len(
            evidence.raw_observation_hashes
        ),
        "raw_observation_contract_hashing": True,
        "canonical_replay_hash_created": (
            evidence.canonical_replay_hash_created
        ),
        "canonical_replay_hash_owned_by_ola_001": True,
        "source_health_status": health.health_status,
        "source_market_identity_preserved": True,
        "event_identity_preserved": True,
        "venue_claim_preserved": True,
        "source_timestamps_preserved": True,
        "fixed_point_price_strings_preserved": True,
        "expiration_fields_preserved": True,
        "occurrence_datetime_preserved": True,
        "cursor_pagination_supported": True,
        "non_200_blocked": True,
        "invalid_json_blocked": True,
        "malformed_market_blocked": True,
        "deterministic_raw_replay_valid": (
            observations == replay_observations
        ),
        "shadow_mode": adapter.shadow_mode,
        "alerts_allowed": adapter.alerts_allowed,
        "qseries_intake_allowed": (
            adapter.qseries_intake_allowed
        ),
        "read_only": adapter.read_only,
        "execution_allowed": adapter.execution_allowed,
        "trade_authorization_allowed": (
            adapter.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            adapter.order_placement_allowed
        ),
        "execution_adapter_invocation_allowed": (
            adapter.execution_adapter_invocation_allowed
        ),
        "funds_moved": adapter.funds_moved,
        "portfolio_mutated": adapter.portfolio_mutated,
    }

    print(
        "[PASS] OLA-016 Oracle Kalshi Public Market "
        "Shadow Source Adapter"
    )

    print(result)


if __name__ == "__main__":
    main()
