from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

PACKAGE_DIR = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
)

MODULE_PATH = (
    PACKAGE_DIR
    / "oracle_kalshi_public_market_shadow_source_adapter.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_016_oracle_kalshi_public_market_shadow_source_adapter.py"
)


MODULE_CONTENT = r'''
"""
OLA-016
Oracle Kalshi Public Market Shadow Source Adapter

FULL RAW OBSERVATION CONTRACT REWRITE

First controlled real-world source adapter for Oracle live acquisition.

Architecture:

KALSHI PUBLIC MARKET DATA
    |
OLA-016 SHADOW SOURCE ADAPTER
    |
FAIL-CLOSED RESPONSE VALIDATION
    |
RAW SOURCE OBSERVATIONS
    |
RAW OBSERVATION STABLE HASH EVIDENCE
    |
OLA-001 LIVE ACQUISITION / CANONICALIZATION
    |
CANONICAL OBSERVATION replay_hash
    |
OLA-003 DEDUPLICATION
    |
OLA-015 POSTGRESQL PERSISTENCE ROUTER
    |
OLA-012 POSTGRESQL BACKEND

Canonical contract boundary:

OLA-016 owns RawSourceObservation records.

RawSourceObservation does not own canonical replay_hash evidence.

OLA-016 computes deterministic raw observation hashes only from the
RawSourceObservation contract:

- source_observation_id
- observed_at
- observation_type
- payload
- provenance

OLA-001 owns CanonicalObservation creation and canonical replay_hash.

Permanent rules:

- Adapter is read-only.
- Adapter uses the public Get Markets endpoint.
- Adapter contains no order endpoint.
- Adapter contains no execution endpoint.
- Adapter contains no portfolio endpoint.
- Adapter contains no API secret.
- Adapter contains no signing key.
- Adapter begins in shadow mode.
- Alerts are disabled.
- Q Series intake is disabled.
- Trade authorization is disabled.
- Order placement is disabled.
- Execution adapter invocation is disabled.
- Funds are never moved.
- Portfolios are never mutated.
- Only HTTP GET acquisition is supported.
- Open markets are collected by default.
- Cursor pagination is explicit.
- Page limit is bounded to 1000.
- Caller supplies acquisition timestamp.
- Source market ticker is preserved.
- Event ticker is preserved.
- Venue claim is explicit.
- Source timestamps are preserved.
- Fixed-point dollar strings are preserved as strings.
- Malformed market records fail closed.
- Malformed pagination fails closed.
- Non-200 responses fail closed.
- Invalid JSON fails closed.
- Raw observation evidence is deterministically hashed.
- Canonical replay hashing remains owned by OLA-001.
- Canonical stable hashing is used.
- repr() is never used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Callable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen


from .oracle_live_read_only_acquisition_runtime import (
    JSONValue,
    RawSourceObservation,
)


SCHEMA_VERSION = "OLA-016"
ENGINE_ID = "OLA-016"

ADAPTER_ID = "adapter.oracle.kalshi.public_markets.shadow"
SOURCE_ID = "source.kalshi.market_data"
VENUE_ID = "venue.kalshi"

PRODUCTION_BASE_URL = (
    "https://external-api.kalshi.com/trade-api/v2"
)

MARKETS_PATH = "/markets"

SUPPORTED_MARKET_STATUSES = (
    "unopened",
    "open",
    "paused",
    "closed",
    "settled",
)

MAX_PAGE_LIMIT = 1000

SHADOW_MODE = True
ALERTS_ALLOWED = False
Q_SERIES_INTAKE_ALLOWED = False


class KalshiShadowAdapterContractError(ValueError):
    """Raised when adapter configuration or source data is malformed."""


class KalshiShadowAdapterSourceError(RuntimeError):
    """Raised when Kalshi source acquisition fails closed."""


class KalshiShadowAdapterInvariantError(RuntimeError):
    """Raised when permanent shadow-mode invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise KalshiShadowAdapterContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise KalshiShadowAdapterContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise KalshiShadowAdapterContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise KalshiShadowAdapterContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(
    value: Any,
) -> JSONValue:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise KalshiShadowAdapterContractError(
                "non-finite floats are not canonical"
            )

        return json.loads(
            json.dumps(
                value,
                allow_nan=False,
            )
        )

    if isinstance(value, datetime):
        return _require_aware_datetime(
            value,
            "canonical datetime",
        ).isoformat()

    if isinstance(value, str):
        return value

    if isinstance(value, Mapping):
        result: dict[str, JSONValue] = {}

        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise KalshiShadowAdapterContractError(
                    "canonical mapping keys must be strings"
                )

            result[key] = _canonicalize(
                value[key]
            )

        return result

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise KalshiShadowAdapterContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(
    value: Any,
) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def raw_observation_canonical_dict(
    observation: RawSourceObservation,
) -> dict[str, Any]:
    if not isinstance(
        observation,
        RawSourceObservation,
    ):
        raise KalshiShadowAdapterContractError(
            "observation must be RawSourceObservation"
        )

    return {
        "source_observation_id": (
            observation.source_observation_id
        ),
        "observed_at": observation.observed_at.isoformat(),
        "observation_type": observation.observation_type,
        "payload": dict(observation.payload),
        "provenance": dict(observation.provenance),
    }


def raw_observation_stable_hash(
    observation: RawSourceObservation,
) -> str:
    return stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "record_type": "kalshi_raw_source_observation",
            "observation": raw_observation_canonical_dict(
                observation
            ),
        }
    )


@dataclass(frozen=True, slots=True)
class KalshiPublicMarketSourceHealthEvidence:
    schema_version: str
    engine_id: str
    adapter_id: str
    source_id: str
    checked_at: datetime
    reachable: bool
    public_endpoint: bool
    authentication_used: bool
    http_method: str
    endpoint_path: str
    shadow_mode: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    health_status: str
    reason_codes: tuple[str, ...]
    evidence_hash: str
    read_only: bool
    execution_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    execution_adapter_invocation_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def to_canonical_dict(
        self,
        *,
        include_evidence_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "adapter_id": self.adapter_id,
            "source_id": self.source_id,
            "checked_at": self.checked_at.isoformat(),
            "reachable": self.reachable,
            "public_endpoint": self.public_endpoint,
            "authentication_used": self.authentication_used,
            "http_method": self.http_method,
            "endpoint_path": self.endpoint_path,
            "shadow_mode": self.shadow_mode,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
            "health_status": self.health_status,
            "reason_codes": list(self.reason_codes),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        if include_evidence_hash:
            result["evidence_hash"] = self.evidence_hash

        return result


@dataclass(frozen=True, slots=True)
class KalshiShadowAcquisitionEvidence:
    schema_version: str
    engine_id: str
    adapter_id: str
    source_id: str
    acquired_at: datetime
    market_status_filter: str
    page_limit: int
    max_pages: int
    pages_requested: int
    source_market_count: int
    observation_count: int
    raw_observation_hashes: tuple[str, ...]
    terminal_cursor_present: bool
    shadow_mode: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    canonical_replay_hash_created: bool
    acquisition_hash: str
    read_only: bool
    execution_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    execution_adapter_invocation_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def to_canonical_dict(
        self,
        *,
        include_acquisition_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "adapter_id": self.adapter_id,
            "source_id": self.source_id,
            "acquired_at": self.acquired_at.isoformat(),
            "market_status_filter": (
                self.market_status_filter
            ),
            "page_limit": self.page_limit,
            "max_pages": self.max_pages,
            "pages_requested": self.pages_requested,
            "source_market_count": self.source_market_count,
            "observation_count": self.observation_count,
            "raw_observation_hashes": list(
                self.raw_observation_hashes
            ),
            "terminal_cursor_present": (
                self.terminal_cursor_present
            ),
            "shadow_mode": self.shadow_mode,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
            "canonical_replay_hash_created": (
                self.canonical_replay_hash_created
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        if include_acquisition_hash:
            result["acquisition_hash"] = (
                self.acquisition_hash
            )

        return result


class _DefaultHTTPFetcher:
    """
    Minimal GET-only transport.

    Returns:
        (status_code, response_body_text)
    """

    def __call__(
        self,
        *,
        url: str,
        timeout_seconds: int,
    ) -> tuple[int, str]:
        request = Request(
            url=url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "QSeries-Oracle-Shadow-Acquisition/OLA-016"
                ),
            },
        )

        with urlopen(
            request,
            timeout=timeout_seconds,
        ) as response:
            status_code = int(
                response.getcode()
            )

            body = response.read().decode(
                "utf-8"
            )

        return status_code, body


class OracleKalshiPublicMarketShadowSourceAdapter:
    """
    OLA-001-compatible public Kalshi source adapter.

    This adapter intentionally begins in observation-only shadow mode.

    acquire(acquired_at=...) returns RawSourceObservation records.

    Raw observation evidence is hashed at this boundary.

    Canonical replay_hash remains owned by OLA-001 after canonicalization.

    No alert emission method exists.
    No Q Series intake method exists.
    No order method exists.
    No execution method exists.
    """

    adapter_id = ADAPTER_ID
    source_id = SOURCE_ID

    read_only = True
    execution_allowed = False

    trade_authorization_allowed = False
    order_placement_allowed = False
    execution_adapter_invocation_allowed = False
    funds_moved = False
    portfolio_mutated = False

    shadow_mode = SHADOW_MODE
    alerts_allowed = ALERTS_ALLOWED
    qseries_intake_allowed = Q_SERIES_INTAKE_ALLOWED

    def __init__(
        self,
        *,
        market_status: str = "open",
        page_limit: int = 1000,
        max_pages: int = 1,
        timeout_seconds: int = 20,
        base_url: str = PRODUCTION_BASE_URL,
        http_fetcher: Callable[..., tuple[int, str]] | None = None,
    ) -> None:
        normalized_status = _require_non_empty_string(
            market_status,
            "market_status",
        )

        if normalized_status not in SUPPORTED_MARKET_STATUSES:
            raise KalshiShadowAdapterContractError(
                "unsupported Kalshi market status"
            )

        if isinstance(page_limit, bool) or not isinstance(
            page_limit,
            int,
        ):
            raise KalshiShadowAdapterContractError(
                "page_limit must be an int"
            )

        if page_limit < 1 or page_limit > MAX_PAGE_LIMIT:
            raise KalshiShadowAdapterContractError(
                "page_limit must be between 1 and 1000"
            )

        if isinstance(max_pages, bool) or not isinstance(
            max_pages,
            int,
        ):
            raise KalshiShadowAdapterContractError(
                "max_pages must be an int"
            )

        if max_pages < 1:
            raise KalshiShadowAdapterContractError(
                "max_pages must be greater than zero"
            )

        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds,
            int,
        ):
            raise KalshiShadowAdapterContractError(
                "timeout_seconds must be an int"
            )

        if timeout_seconds < 1:
            raise KalshiShadowAdapterContractError(
                "timeout_seconds must be greater than zero"
            )

        normalized_base_url = _require_non_empty_string(
            base_url,
            "base_url",
        ).rstrip("/")

        fetcher = (
            _DefaultHTTPFetcher()
            if http_fetcher is None
            else http_fetcher
        )

        if not callable(fetcher):
            raise KalshiShadowAdapterContractError(
                "http_fetcher must be callable"
            )

        self._market_status = normalized_status
        self._page_limit = page_limit
        self._max_pages = max_pages
        self._timeout_seconds = timeout_seconds
        self._base_url = normalized_base_url
        self._http_fetcher = fetcher

        self._last_acquisition_evidence: (
            KalshiShadowAcquisitionEvidence | None
        ) = None

        self._assert_invariants()

    def _assert_invariants(self) -> None:
        actual = {
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
            "shadow_mode": self.shadow_mode,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
        }

        expected = {
            "read_only": True,
            "execution_allowed": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "execution_adapter_invocation_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
            "shadow_mode": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
        }

        if actual != expected:
            raise KalshiShadowAdapterInvariantError(
                "Kalshi shadow adapter invariants violated"
            )

    @property
    def market_status(self) -> str:
        return self._market_status

    @property
    def page_limit(self) -> int:
        return self._page_limit

    @property
    def max_pages(self) -> int:
        return self._max_pages

    @property
    def last_acquisition_evidence(
        self,
    ) -> KalshiShadowAcquisitionEvidence | None:
        return self._last_acquisition_evidence

    def probe_health(
        self,
        *,
        checked_at: datetime,
    ) -> KalshiPublicMarketSourceHealthEvidence:
        self._assert_invariants()

        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )

        reachable = False

        try:
            status_code, body = self._fetch_page(
                cursor=None,
            )

            if status_code == 200:
                self._decode_markets_response(
                    body
                )

                reachable = True

        except (
            KalshiShadowAdapterSourceError,
            KalshiShadowAdapterContractError,
        ):
            reachable = False

        health_status = (
            "healthy"
            if reachable
            else "unhealthy"
        )

        reason_codes = (
            (
                "public_markets_endpoint_reachable",
                "public_response_contract_valid",
                "shadow_source_healthy",
            )
            if reachable
            else (
                "public_markets_endpoint_unhealthy",
                "shadow_source_unhealthy",
            )
        )

        provisional = KalshiPublicMarketSourceHealthEvidence(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            adapter_id=self.adapter_id,
            source_id=self.source_id,
            checked_at=normalized_checked_at,
            reachable=reachable,
            public_endpoint=True,
            authentication_used=False,
            http_method="GET",
            endpoint_path=MARKETS_PATH,
            shadow_mode=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            health_status=health_status,
            reason_codes=reason_codes,
            evidence_hash="",
            read_only=True,
            execution_allowed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        evidence_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": (
                    "kalshi_public_market_source_health_evidence"
                ),
                "evidence": provisional.to_canonical_dict(
                    include_evidence_hash=False
                ),
            }
        )

        return KalshiPublicMarketSourceHealthEvidence(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            adapter_id=provisional.adapter_id,
            source_id=provisional.source_id,
            checked_at=provisional.checked_at,
            reachable=provisional.reachable,
            public_endpoint=True,
            authentication_used=False,
            http_method="GET",
            endpoint_path=MARKETS_PATH,
            shadow_mode=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            health_status=provisional.health_status,
            reason_codes=provisional.reason_codes,
            evidence_hash=evidence_hash,
            read_only=True,
            execution_allowed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    def acquire(
        self,
        *,
        acquired_at: datetime,
    ) -> tuple[RawSourceObservation, ...]:
        self._assert_invariants()

        normalized_acquired_at = _require_aware_datetime(
            acquired_at,
            "acquired_at",
        )

        observations: list[
            RawSourceObservation
        ] = []

        seen_tickers: set[str] = set()

        cursor: str | None = None

        pages_requested = 0

        terminal_cursor_present = False

        while pages_requested < self._max_pages:
            status_code, body = self._fetch_page(
                cursor=cursor,
            )

            if status_code != 200:
                raise KalshiShadowAdapterSourceError(
                    "Kalshi Get Markets returned non-200 response"
                )

            markets, next_cursor = (
                self._decode_markets_response(
                    body
                )
            )

            pages_requested += 1

            for market in markets:
                observation = self._market_to_observation(
                    market=market,
                    acquired_at=normalized_acquired_at,
                )

                ticker = dict(
                    observation.payload
                )["source_market_id"]

                if ticker in seen_tickers:
                    continue

                seen_tickers.add(
                    ticker
                )

                observations.append(
                    observation
                )

            if next_cursor is None:
                cursor = None
                terminal_cursor_present = False

                break

            cursor = next_cursor
            terminal_cursor_present = True

        raw_observation_hashes = tuple(
            raw_observation_stable_hash(
                observation
            )
            for observation in observations
        )

        provisional = KalshiShadowAcquisitionEvidence(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            adapter_id=self.adapter_id,
            source_id=self.source_id,
            acquired_at=normalized_acquired_at,
            market_status_filter=self._market_status,
            page_limit=self._page_limit,
            max_pages=self._max_pages,
            pages_requested=pages_requested,
            source_market_count=len(seen_tickers),
            observation_count=len(observations),
            raw_observation_hashes=raw_observation_hashes,
            terminal_cursor_present=(
                terminal_cursor_present
            ),
            shadow_mode=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            canonical_replay_hash_created=False,
            acquisition_hash="",
            read_only=True,
            execution_allowed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        acquisition_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": (
                    "kalshi_shadow_acquisition_evidence"
                ),
                "evidence": provisional.to_canonical_dict(
                    include_acquisition_hash=False
                ),
            }
        )

        self._last_acquisition_evidence = (
            KalshiShadowAcquisitionEvidence(
                schema_version=provisional.schema_version,
                engine_id=provisional.engine_id,
                adapter_id=provisional.adapter_id,
                source_id=provisional.source_id,
                acquired_at=provisional.acquired_at,
                market_status_filter=(
                    provisional.market_status_filter
                ),
                page_limit=provisional.page_limit,
                max_pages=provisional.max_pages,
                pages_requested=provisional.pages_requested,
                source_market_count=(
                    provisional.source_market_count
                ),
                observation_count=(
                    provisional.observation_count
                ),
                raw_observation_hashes=(
                    provisional.raw_observation_hashes
                ),
                terminal_cursor_present=(
                    provisional.terminal_cursor_present
                ),
                shadow_mode=True,
                alerts_allowed=False,
                qseries_intake_allowed=False,
                canonical_replay_hash_created=False,
                acquisition_hash=acquisition_hash,
                read_only=True,
                execution_allowed=False,
                trade_authorization_allowed=False,
                order_placement_allowed=False,
                execution_adapter_invocation_allowed=False,
                funds_moved=False,
                portfolio_mutated=False,
            )
        )

        return tuple(
            observations
        )

    def _fetch_page(
        self,
        *,
        cursor: str | None,
    ) -> tuple[int, str]:
        params = {
            "limit": self._page_limit,
            "status": self._market_status,
        }

        if cursor is not None:
            params["cursor"] = cursor

        url = (
            self._base_url
            + MARKETS_PATH
            + "?"
            + urlencode(params)
        )

        try:
            result = self._http_fetcher(
                url=url,
                timeout_seconds=self._timeout_seconds,
            )

        except Exception as exc:
            raise KalshiShadowAdapterSourceError(
                "Kalshi public market request failed closed"
            ) from exc

        if (
            not isinstance(result, tuple)
            or len(result) != 2
        ):
            raise KalshiShadowAdapterSourceError(
                "HTTP fetcher returned incompatible result"
            )

        status_code, body = result

        if isinstance(status_code, bool) or not isinstance(
            status_code,
            int,
        ):
            raise KalshiShadowAdapterSourceError(
                "HTTP status code is incompatible"
            )

        if not isinstance(body, str):
            raise KalshiShadowAdapterSourceError(
                "HTTP response body must be text"
            )

        return status_code, body

    @staticmethod
    def _decode_markets_response(
        body: str,
    ) -> tuple[
        tuple[dict[str, Any], ...],
        str | None,
    ]:
        try:
            data = json.loads(
                body
            )

        except json.JSONDecodeError as exc:
            raise KalshiShadowAdapterSourceError(
                "Kalshi Get Markets returned invalid JSON"
            ) from exc

        if not isinstance(data, dict):
            raise KalshiShadowAdapterSourceError(
                "Kalshi Get Markets response must be a mapping"
            )

        allowed_top_level_fields = {
            "markets",
            "cursor",
        }

        if not set(data.keys()).issubset(
            allowed_top_level_fields
        ):
            raise KalshiShadowAdapterSourceError(
                "Kalshi Get Markets response contains "
                "unexpected top-level fields"
            )

        if "markets" not in data:
            raise KalshiShadowAdapterSourceError(
                "Kalshi Get Markets response lacks markets"
            )

        markets = data["markets"]

        if not isinstance(markets, list):
            raise KalshiShadowAdapterSourceError(
                "markets must be a list"
            )

        normalized_markets = []

        for market in markets:
            if not isinstance(market, dict):
                raise KalshiShadowAdapterSourceError(
                    "market record must be a mapping"
                )

            normalized_markets.append(
                dict(market)
            )

        cursor = data.get(
            "cursor"
        )

        if cursor in (
            None,
            "",
        ):
            normalized_cursor = None

        elif isinstance(cursor, str):
            normalized_cursor = cursor

        else:
            raise KalshiShadowAdapterSourceError(
                "cursor must be text or empty"
            )

        return (
            tuple(normalized_markets),
            normalized_cursor,
        )

    def _market_to_observation(
        self,
        *,
        market: Mapping[str, Any],
        acquired_at: datetime,
    ) -> RawSourceObservation:
        ticker = _require_non_empty_string(
            market.get("ticker"),
            "market.ticker",
        )

        event_ticker = _require_non_empty_string(
            market.get("event_ticker"),
            "market.event_ticker",
        )

        title = _require_non_empty_string(
            market.get("title"),
            "market.title",
        )

        source_observed_at = self._resolve_source_observed_at(
            market
        )

        payload = {
            "source_market_id": ticker,
            "source_symbol": ticker,
            "event_ticker": event_ticker,
            "instrument_type": "prediction_contract",
            "market_title": title,
            "subtitle": market.get("subtitle"),
            "yes_sub_title": market.get("yes_sub_title"),
            "no_sub_title": market.get("no_sub_title"),
            "venue_claim": VENUE_ID,
            "source_status_filter": self._market_status,
            "source_created_time": market.get("created_time"),
            "source_updated_time": market.get("updated_time"),
            "source_open_time": market.get("open_time"),
            "source_close_time": market.get("close_time"),
            "source_latest_expiration_time": (
                market.get("latest_expiration_time")
            ),
            "source_expected_expiration_time": (
                market.get("expected_expiration_time")
            ),
            "source_expiration_time": (
                market.get("expiration_time")
            ),
            "source_occurrence_datetime": (
                market.get("occurrence_datetime")
            ),
            "yes_bid_dollars": market.get("yes_bid_dollars"),
            "yes_bid_size_fp": market.get("yes_bid_size_fp"),
            "yes_ask_dollars": market.get("yes_ask_dollars"),
            "yes_ask_size_fp": market.get("yes_ask_size_fp"),
            "no_bid_dollars": market.get("no_bid_dollars"),
            "no_ask_dollars": market.get("no_ask_dollars"),
            "last_price_dollars": market.get(
                "last_price_dollars"
            ),
            "previous_yes_bid_dollars": market.get(
                "previous_yes_bid_dollars"
            ),
            "previous_yes_ask_dollars": market.get(
                "previous_yes_ask_dollars"
            ),
            "previous_price_dollars": market.get(
                "previous_price_dollars"
            ),
            "volume_fp": market.get("volume_fp"),
            "volume_24h_fp": market.get("volume_24h_fp"),
            "open_interest_fp": market.get("open_interest_fp"),
            "liquidity_dollars": market.get(
                "liquidity_dollars"
            ),
            "notional_value_dollars": market.get(
                "notional_value_dollars"
            ),
            "can_close_early": market.get("can_close_early"),
            "early_close_condition": market.get(
                "early_close_condition"
            ),
            "settlement_timer_seconds": market.get(
                "settlement_timer_seconds"
            ),
            "rules_primary": market.get("rules_primary"),
            "rules_secondary": market.get("rules_secondary"),
            "price_level_structure": market.get(
                "price_level_structure"
            ),
            "floor_strike": market.get("floor_strike"),
            "cap_strike": market.get("cap_strike"),
            "functional_strike": market.get(
                "functional_strike"
            ),
            "is_provisional": market.get("is_provisional"),
            "exchange_index": market.get("exchange_index"),
            "shadow_mode": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
        }

        canonical_payload = _canonicalize(
            payload
        )

        if not isinstance(
            canonical_payload,
            dict,
        ):
            raise KalshiShadowAdapterContractError(
                "market payload failed canonicalization"
            )

        provenance = {
            "source_id": SOURCE_ID,
            "adapter_id": ADAPTER_ID,
            "venue_id": VENUE_ID,
            "source_environment": "production",
            "source_api": "kalshi_trade_api_v2",
            "source_endpoint": MARKETS_PATH,
            "http_method": "GET",
            "public_endpoint": True,
            "authentication_used": False,
            "shadow_mode": True,
            "acquired_at": acquired_at.isoformat(),
        }

        return RawSourceObservation.create(
            source_observation_id=(
                "kalshi.market."
                + ticker
                + "."
                + stable_hash(
                    {
                        "ticker": ticker,
                        "source_observed_at": (
                            source_observed_at
                        ),
                        "payload": canonical_payload,
                    }
                )
            ),
            observed_at=source_observed_at,
            observation_type="market_snapshot",
            payload=canonical_payload,
            provenance=provenance,
        )

    @staticmethod
    def _resolve_source_observed_at(
        market: Mapping[str, Any],
    ) -> datetime:
        for field_name in (
            "updated_time",
            "created_time",
            "open_time",
        ):
            value = market.get(
                field_name
            )

            if value is None:
                continue

            if not isinstance(value, str):
                raise KalshiShadowAdapterContractError(
                    f"market.{field_name} must be text"
                )

            normalized = value.strip()

            if not normalized:
                continue

            try:
                parsed = datetime.fromisoformat(
                    normalized.replace(
                        "Z",
                        "+00:00",
                    )
                )

            except ValueError as exc:
                raise KalshiShadowAdapterContractError(
                    f"market.{field_name} is not ISO-8601"
                ) from exc

            return _require_aware_datetime(
                parsed,
                f"market.{field_name}",
            )

        raise KalshiShadowAdapterContractError(
            "market lacks a usable source observation timestamp"
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ADAPTER_ID",
    "SOURCE_ID",
    "VENUE_ID",
    "PRODUCTION_BASE_URL",
    "MARKETS_PATH",
    "SUPPORTED_MARKET_STATUSES",
    "MAX_PAGE_LIMIT",
    "SHADOW_MODE",
    "ALERTS_ALLOWED",
    "Q_SERIES_INTAKE_ALLOWED",
    "KalshiShadowAdapterContractError",
    "KalshiShadowAdapterSourceError",
    "KalshiShadowAdapterInvariantError",
    "KalshiPublicMarketSourceHealthEvidence",
    "KalshiShadowAcquisitionEvidence",
    "OracleKalshiPublicMarketShadowSourceAdapter",
    "canonical_json",
    "stable_hash",
    "raw_observation_canonical_dict",
    "raw_observation_stable_hash",
]
'''


TEST_CONTENT = r'''
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
'''


EXPORT_BLOCK = r'''

from .oracle_kalshi_public_market_shadow_source_adapter import (
    ADAPTER_ID as KALSHI_SHADOW_ADAPTER_ID,
    ALERTS_ALLOWED as KALSHI_SHADOW_ALERTS_ALLOWED,
    MAX_PAGE_LIMIT as KALSHI_SHADOW_MAX_PAGE_LIMIT,
    MARKETS_PATH as KALSHI_PUBLIC_MARKETS_PATH,
    PRODUCTION_BASE_URL as KALSHI_PRODUCTION_BASE_URL,
    Q_SERIES_INTAKE_ALLOWED as KALSHI_SHADOW_Q_SERIES_INTAKE_ALLOWED,
    SHADOW_MODE as KALSHI_SHADOW_MODE,
    SOURCE_ID as KALSHI_MARKET_DATA_SOURCE_ID,
    SUPPORTED_MARKET_STATUSES as KALSHI_SUPPORTED_MARKET_STATUSES,
    VENUE_ID as KALSHI_VENUE_ID,
    KalshiPublicMarketSourceHealthEvidence,
    KalshiShadowAcquisitionEvidence,
    KalshiShadowAdapterContractError,
    KalshiShadowAdapterInvariantError,
    KalshiShadowAdapterSourceError,
    OracleKalshiPublicMarketShadowSourceAdapter,
    raw_observation_canonical_dict,
    raw_observation_stable_hash,
)
'''


EXPORT_NAMES = [
    "KALSHI_SHADOW_ADAPTER_ID",
    "KALSHI_SHADOW_ALERTS_ALLOWED",
    "KALSHI_SHADOW_MAX_PAGE_LIMIT",
    "KALSHI_PUBLIC_MARKETS_PATH",
    "KALSHI_PRODUCTION_BASE_URL",
    "KALSHI_SHADOW_Q_SERIES_INTAKE_ALLOWED",
    "KALSHI_SHADOW_MODE",
    "KALSHI_MARKET_DATA_SOURCE_ID",
    "KALSHI_SUPPORTED_MARKET_STATUSES",
    "KALSHI_VENUE_ID",
    "KalshiPublicMarketSourceHealthEvidence",
    "KalshiShadowAcquisitionEvidence",
    "KalshiShadowAdapterContractError",
    "KalshiShadowAdapterInvariantError",
    "KalshiShadowAdapterSourceError",
    "OracleKalshiPublicMarketShadowSourceAdapter",
    "raw_observation_canonical_dict",
    "raw_observation_stable_hash",
]


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


def update_package_exports() -> None:
    existing = PACKAGE_INIT_PATH.read_text(
        encoding="utf-8"
    )

    import_marker = (
        "from .oracle_kalshi_public_market_shadow_"
        "source_adapter import"
    )

    updated = existing

    if import_marker in updated:
        import_start = updated.index(
            import_marker
        )

        import_end = updated.index(
            "\n)",
            import_start,
        ) + 2

        updated = (
            updated[:import_start]
            + textwrap.dedent(EXPORT_BLOCK).lstrip()
            + updated[import_end:]
        )

    else:
        updated = (
            updated.rstrip()
            + "\n"
            + textwrap.dedent(EXPORT_BLOCK)
        )

    all_start = updated.find("__all__ = [")

    if all_start == -1:
        raise RuntimeError(
            "__init__.py does not contain __all__"
        )

    closing_index = updated.find(
        "]",
        all_start,
    )

    if closing_index == -1:
        raise RuntimeError(
            "__init__.py does not contain __all__ closing bracket"
        )

    for name in EXPORT_NAMES:
        export_line = f'    "{name}",'

        if export_line in updated[
            all_start:closing_index
        ]:
            continue

        updated = (
            updated[:closing_index]
            + export_line
            + "\n"
            + updated[closing_index:]
        )

        closing_index += len(
            export_line
        ) + 1

    PACKAGE_INIT_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        f"[OK] Updated {PACKAGE_INIT_PATH}"
    )


def main() -> None:
    print("========================================")
    print(" OLA-016 INSTALLER")
    print(" Oracle Kalshi Public Market")
    print(" Shadow Source Adapter")
    print(" FULL RAW OBSERVATION CONTRACT REWRITE")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    update_package_exports()

    print()
    print("[DONE] OLA-016 rewritten")
    print()
    print("Run:")
    print(
        "py test_ola_016_oracle_kalshi_public_market_"
        "shadow_source_adapter.py"
    )


if __name__ == "__main__":
    main()