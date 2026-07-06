from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
MODULE_PATH = MODULE_DIR / "universal_market_adapter_discovery_engine.py"
TEST_PATH = ROOT / "test_oi_176_universal_market_adapter_discovery_engine.py"
INIT_PATH = MODULE_DIR / "__init__.py"

MODULE_CODE = r'''
"""
OI-176 — Oracle Universal Market Adapter Discovery Engine

Production-grade, read-only discovery layer for Universal Market Model adapter
candidates.

This engine discovers adapter opportunities across configured market domains,
normalizes discovery evidence, scores adapter readiness, explains every result,
and emits replayable telemetry snapshots without executing trades, submitting
orders, managing positions, or mutating external systems.

Oracle remains intelligence-only. Q Series remains the sole execution owner.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


ENGINE_ID = "oi.176.universal_market_adapter_discovery"
ENGINE_NAME = "Oracle Universal Market Adapter Discovery Engine"
ENGINE_VERSION = "1.0.0"
ARCHITECTURE_ROLE = "read_only_adapter_discovery"
Q_SERIES_EXECUTION_OWNER = "qseries.execution"


SUPPORTED_MARKETS: Tuple[str, ...] = (
    "prediction_markets",
    "crypto",
    "stocks",
    "etfs",
    "futures",
    "commodities",
    "forex",
    "macroeconomics",
    "weather",
    "news",
    "alternative_data",
)


READ_ONLY_GUARDRAILS: Tuple[str, ...] = (
    "Oracle never executes trades.",
    "Oracle never manages positions.",
    "Oracle never submits orders.",
    "Oracle never routes orders.",
    "Oracle never signs transactions.",
    "Oracle never custody-controls assets.",
    "Q Series is the only execution engine.",
)


DISCOVERY_SIGNAL_WEIGHTS: Mapping[str, float] = {
    "schema_available": 0.17,
    "market_identifier_available": 0.14,
    "timestamp_available": 0.10,
    "price_or_probability_available": 0.13,
    "liquidity_available": 0.10,
    "status_available": 0.08,
    "historical_snapshots_available": 0.10,
    "rate_limit_known": 0.06,
    "terms_known": 0.05,
    "health_probe_available": 0.07,
}


REQUIRED_UMM_FIELDS: Tuple[str, ...] = (
    "market_id",
    "market_type",
    "title",
    "status",
    "timestamp",
)


OPTIONAL_UMM_FIELDS: Tuple[str, ...] = (
    "exchange",
    "symbol",
    "event_id",
    "outcomes",
    "best_bid",
    "best_ask",
    "last_price",
    "probability",
    "volume",
    "open_interest",
    "liquidity",
    "expiry",
    "settlement_source",
    "source_url",
    "raw_payload_hash",
)


MARKET_FIELD_HINTS: Mapping[str, Tuple[str, ...]] = {
    "prediction_markets": (
        "event_id",
        "market_id",
        "outcomes",
        "probability",
        "best_bid",
        "best_ask",
        "expiry",
        "settlement_source",
    ),
    "crypto": (
        "symbol",
        "exchange",
        "best_bid",
        "best_ask",
        "last_price",
        "volume",
        "liquidity",
    ),
    "stocks": (
        "symbol",
        "exchange",
        "last_price",
        "volume",
        "timestamp",
    ),
    "etfs": (
        "symbol",
        "exchange",
        "last_price",
        "volume",
        "timestamp",
    ),
    "futures": (
        "symbol",
        "exchange",
        "expiry",
        "last_price",
        "volume",
        "open_interest",
    ),
    "commodities": (
        "symbol",
        "exchange",
        "last_price",
        "volume",
        "timestamp",
    ),
    "forex": (
        "symbol",
        "exchange",
        "best_bid",
        "best_ask",
        "last_price",
        "timestamp",
    ),
    "macroeconomics": (
        "event_id",
        "title",
        "timestamp",
        "settlement_source",
        "source_url",
    ),
    "weather": (
        "event_id",
        "title",
        "timestamp",
        "settlement_source",
        "source_url",
    ),
    "news": (
        "event_id",
        "title",
        "timestamp",
        "source_url",
    ),
    "alternative_data": (
        "event_id",
        "title",
        "timestamp",
        "source_url",
    ),
}


@dataclass(frozen=True)
class AdapterDiscoverySource:
    """
    Description of a potential adapter source.

    The source may describe an API, local replay file, websocket metadata feed,
    vendor export, registry item, documentation source, or manually curated
    adapter candidate.

    This object is descriptive only. It does not perform network requests.
    """

    source_id: str
    name: str
    market_type: str
    source_kind: str
    endpoint: Optional[str] = None
    documentation_url: Optional[str] = None
    owner: Optional[str] = None
    schema_fields: Tuple[str, ...] = field(default_factory=tuple)
    sample_payload: Optional[Mapping[str, Any]] = None
    rate_limit: Optional[str] = None
    terms_status: Optional[str] = None
    historical_available: bool = False
    health_probe: Optional[str] = None
    enabled: bool = True
    notes: Tuple[str, ...] = field(default_factory=tuple)

    def normalized_market_type(self) -> str:
        return normalize_market_type(self.market_type)

    def fingerprint(self) -> str:
        body = {
            "source_id": self.source_id,
            "name": self.name,
            "market_type": self.normalized_market_type(),
            "source_kind": self.source_kind,
            "endpoint": self.endpoint,
            "documentation_url": self.documentation_url,
            "schema_fields": list(self.schema_fields),
            "rate_limit": self.rate_limit,
            "terms_status": self.terms_status,
            "historical_available": self.historical_available,
            "health_probe": self.health_probe,
            "enabled": self.enabled,
        }
        return stable_hash(body)


@dataclass(frozen=True)
class AdapterDiscoveryEvidence:
    source_id: str
    discovered_at: float
    signal_map: Mapping[str, bool]
    required_umm_coverage: Mapping[str, bool]
    optional_umm_coverage: Mapping[str, bool]
    market_specific_coverage: Mapping[str, bool]
    source_fingerprint: str
    payload_fingerprint: Optional[str]
    warnings: Tuple[str, ...]
    guardrails: Tuple[str, ...] = READ_ONLY_GUARDRAILS

    def readiness_score(self) -> float:
        score = 0.0
        for signal, weight in DISCOVERY_SIGNAL_WEIGHTS.items():
            if self.signal_map.get(signal, False):
                score += weight

        required_values = list(self.required_umm_coverage.values())
        if required_values:
            required_ratio = sum(1 for value in required_values if value) / len(required_values)
        else:
            required_ratio = 0.0

        market_values = list(self.market_specific_coverage.values())
        if market_values:
            market_ratio = sum(1 for value in market_values if value) / len(market_values)
        else:
            market_ratio = 0.0

        score = (score * 0.70) + (required_ratio * 0.20) + (market_ratio * 0.10)

        if self.warnings:
            score -= min(0.18, 0.03 * len(self.warnings))

        return round(max(0.0, min(1.0, score)), 6)

    def classification(self) -> str:
        score = self.readiness_score()
        if score >= 0.86:
            return "adapter_ready"
        if score >= 0.70:
            return "adapter_candidate"
        if score >= 0.50:
            return "research_required"
        return "not_ready"


@dataclass(frozen=True)
class AdapterDiscoveryResult:
    engine_id: str
    engine_version: str
    source: AdapterDiscoverySource
    evidence: AdapterDiscoveryEvidence
    readiness_score: float
    classification: str
    explanation: Mapping[str, Any]
    replay_key: str
    telemetry: Mapping[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "source": source_to_dict(self.source),
            "evidence": evidence_to_dict(self.evidence),
            "readiness_score": self.readiness_score,
            "classification": self.classification,
            "explanation": dict(self.explanation),
            "replay_key": self.replay_key,
            "telemetry": dict(self.telemetry),
        }
        return data


@dataclass(frozen=True)
class AdapterDiscoverySnapshot:
    engine_id: str
    engine_name: str
    engine_version: str
    created_at: float
    market_scope: Tuple[str, ...]
    result_count: int
    results: Tuple[AdapterDiscoveryResult, ...]
    architecture: Mapping[str, Any]
    replay_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "created_at": self.created_at,
            "market_scope": list(self.market_scope),
            "result_count": self.result_count,
            "results": [result.to_dict() for result in self.results],
            "architecture": dict(self.architecture),
            "replay_hash": self.replay_hash,
        }


def normalize_market_type(value: str) -> str:
    cleaned = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "prediction": "prediction_markets",
        "prediction_market": "prediction_markets",
        "prediction_markets": "prediction_markets",
        "crypto_currency": "crypto",
        "cryptocurrency": "crypto",
        "digital_assets": "crypto",
        "equity": "stocks",
        "equities": "stocks",
        "stock": "stocks",
        "exchange_traded_funds": "etfs",
        "etf": "etfs",
        "future": "futures",
        "commodity": "commodities",
        "fx": "forex",
        "foreign_exchange": "forex",
        "macro": "macroeconomics",
        "economic": "macroeconomics",
        "weather_markets": "weather",
        "news_markets": "news",
        "alt_data": "alternative_data",
        "alternative": "alternative_data",
    }
    return aliases.get(cleaned, cleaned)


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_to_dict(source: AdapterDiscoverySource) -> Dict[str, Any]:
    return {
        "source_id": source.source_id,
        "name": source.name,
        "market_type": source.normalized_market_type(),
        "source_kind": source.source_kind,
        "endpoint": source.endpoint,
        "documentation_url": source.documentation_url,
        "owner": source.owner,
        "schema_fields": list(source.schema_fields),
        "sample_payload": dict(source.sample_payload or {}),
        "rate_limit": source.rate_limit,
        "terms_status": source.terms_status,
        "historical_available": source.historical_available,
        "health_probe": source.health_probe,
        "enabled": source.enabled,
        "notes": list(source.notes),
        "fingerprint": source.fingerprint(),
    }


def evidence_to_dict(evidence: AdapterDiscoveryEvidence) -> Dict[str, Any]:
    return {
        "source_id": evidence.source_id,
        "discovered_at": evidence.discovered_at,
        "signal_map": dict(evidence.signal_map),
        "required_umm_coverage": dict(evidence.required_umm_coverage),

        "optional_umm_coverage": dict(evidence.optional_umm_coverage),
        "market_specific_coverage": dict(evidence.market_specific_coverage),
        "source_fingerprint": evidence.source_fingerprint,
        "payload_fingerprint": evidence.payload_fingerprint,
        "warnings": list(evidence.warnings),
        "guardrails": list(evidence.guardrails),
        "readiness_score": evidence.readiness_score(),
        "classification": evidence.classification(),
    }


def extract_field_names(source: AdapterDiscoverySource) -> Tuple[str, ...]:
    fields = set(str(field).strip() for field in source.schema_fields if str(field).strip())

    if source.sample_payload:
        fields.update(flatten_payload_keys(source.sample_payload))

    return tuple(sorted(fields))


def flatten_payload_keys(payload: Mapping[str, Any], prefix: str = "") -> Tuple[str, ...]:
    keys: List[str] = []

    for key, value in payload.items():
        key_text = str(key).strip()
        if not key_text:
            continue

        full_key = f"{prefix}.{key_text}" if prefix else key_text
        keys.append(key_text)
        keys.append(full_key)

        if isinstance(value, Mapping):
            keys.extend(flatten_payload_keys(value, full_key))
        elif isinstance(value, list) and value and isinstance(value[0], Mapping):
            keys.extend(flatten_payload_keys(value[0], full_key))

    return tuple(sorted(set(keys)))


def has_any_field(fields: Iterable[str], candidates: Iterable[str]) -> bool:
    field_set = {str(field).lower() for field in fields}
    for candidate in candidates:
        candidate_lower = str(candidate).lower()
        if candidate_lower in field_set:
            return True
        for field in field_set:
            if field.endswith("." + candidate_lower):
                return True
    return False


def build_signal_map(source: AdapterDiscoverySource, fields: Sequence[str]) -> Dict[str, bool]:
    return {
        "schema_available": bool(fields),
        "market_identifier_available": has_any_field(fields, ("market_id", "id", "ticker", "symbol")),
        "timestamp_available": has_any_field(fields, ("timestamp", "time", "created_at", "updated_at", "last_update")),
        "price_or_probability_available": has_any_field(
            fields,
            (
                "price",
                "last_price",
                "best_bid",
                "best_ask",
                "probability",
                "yes_price",
                "no_price",
                "mark_price",
            ),
        ),
        "liquidity_available": has_any_field(fields, ("liquidity", "volume", "open_interest", "depth")),
        "status_available": has_any_field(fields, ("status", "state", "active", "tradable")),
        "historical_snapshots_available": bool(source.historical_available),
        "rate_limit_known": bool(source.rate_limit),
        "terms_known": bool(source.terms_status),
        "health_probe_available": bool(source.health_probe),
    }


def build_coverage(fields: Sequence[str], required: Sequence[str]) -> Dict[str, bool]:
    coverage: Dict[str, bool] = {}

    for field_name in required:
        aliases = field_aliases(field_name)
        coverage[field_name] = has_any_field(fields, aliases)

    return coverage


def field_aliases(field_name: str) -> Tuple[str, ...]:
    aliases = {
        "market_id": ("market_id", "id", "ticker", "symbol", "instrument_id"),
        "market_type": ("market_type", "asset_class", "category", "domain"),
        "title": ("title", "name", "description", "question"),
        "status": ("status", "state", "active", "tradable"),
        "timestamp": ("timestamp", "time", "created_at", "updated_at", "last_update"),
        "exchange": ("exchange", "venue", "platform"),
        "symbol": ("symbol", "ticker", "base_symbol", "instrument"),
        "event_id": ("event_id", "event", "series_id"),
        "outcomes": ("outcomes", "contracts", "legs", "options"),
        "best_bid": ("best_bid", "bid", "yes_bid", "bid_price"),
        "best_ask": ("best_ask", "ask", "yes_ask", "ask_price"),
        "last_price": ("last_price", "price", "mark_price", "close"),
        "probability": ("probability", "implied_probability", "yes_price"),
        "volume": ("volume", "vol", "turnover"),
        "open_interest": ("open_interest", "oi"),
        "liquidity": ("liquidity", "depth"),
        "expiry": ("expiry", "expiration", "close_time", "end_time"),
        "settlement_source": ("settlement_source", "resolution_source", "data_source"),
        "source_url": ("source_url", "url", "link"),
        "raw_payload_hash": ("raw_payload_hash", "payload_hash"),
    }
    return aliases.get(field_name, (field_name,))


def build_warnings(source: AdapterDiscoverySource, signal_map: Mapping[str, bool], required_coverage: Mapping[str, bool]) -> Tuple[str, ...]:
    warnings: List[str] = []

    market_type = source.normalized_market_type()
    if market_type not in SUPPORTED_MARKETS:
        warnings.append(f"unsupported_market_type:{market_type}")

    if not source.enabled:
        warnings.append("source_disabled")

    if not signal_map.get("schema_available", False):
        warnings.append("missing_schema_or_sample_payload")

    missing_required = [name for name, present in required_coverage.items() if not present]
    if missing_required:
        warnings.append("missing_required_umm_fields:" + ",".join(missing_required))

    if not signal_map.get("terms_known", False):
        warnings.append("terms_status_unknown")

    if not signal_map.get("rate_limit_known", False):
        warnings.append("rate_limit_unknown")

    if not signal_map.get("health_probe_available", False):
        warnings.append("health_probe_missing")

    return tuple(warnings)


def discover_source(source: AdapterDiscoverySource, discovered_at: Optional[float] = None) -> AdapterDiscoveryResult:
    timestamp = float(discovered_at if discovered_at is not None else time.time())
    fields = extract_field_names(source)
    market_type = source.normalized_market_type()

    signal_map = build_signal_map(source, fields)
    required_coverage = build_coverage(fields, REQUIRED_UMM_FIELDS)
    optional_coverage = build_coverage(fields, OPTIONAL_UMM_FIELDS)
    market_specific_fields = MARKET_FIELD_HINTS.get(market_type, ())
    market_specific_coverage = build_coverage(fields, market_specific_fields)
    warnings = build_warnings(source, signal_map, required_coverage)

    payload_fingerprint = stable_hash(source.sample_payload) if source.sample_payload else None

    evidence = AdapterDiscoveryEvidence(
        source_id=source.source_id,
        discovered_at=timestamp,
        signal_map=signal_map,
        required_umm_coverage=required_coverage,
        optional_umm_coverage=optional_coverage,
        market_specific_coverage=market_specific_coverage,
        source_fingerprint=source.fingerprint(),
        payload_fingerprint=payload_fingerprint,
        warnings=warnings,
    )

    readiness_score = evidence.readiness_score()
    classification = evidence.classification()

    explanation = build_explanation(
        source=source,
        fields=fields,
        evidence=evidence,
        readiness_score=readiness_score,
        classification=classification,
    )

    replay_key = stable_hash(
        {
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "source_fingerprint": source.fingerprint(),
            "payload_fingerprint": payload_fingerprint,
            "readiness_score": readiness_score,
            "classification": classification,
            "warnings": warnings,
        }
    )

    telemetry = build_telemetry(source, evidence, readiness_score, classification, replay_key)

    return AdapterDiscoveryResult(
        engine_id=ENGINE_ID,
        engine_version=ENGINE_VERSION,
        source=source,
        evidence=evidence,
        readiness_score=readiness_score,
        classification=classification,
        explanation=explanation,
        replay_key=replay_key,
        telemetry=telemetry,
    )


def build_explanation(
    source: AdapterDiscoverySource,
    fields: Sequence[str],
    evidence: AdapterDiscoveryEvidence,
    readiness_score: float,
    classification: str,
) -> Dict[str, Any]:
    required_present = [name for name, present in evidence.required_umm_coverage.items() if present]
    required_missing = [name for name, present in evidence.required_umm_coverage.items() if not present]
    signals_present = [name for name, present in evidence.signal_map.items() if present]
    signals_missing = [name for name, present in evidence.signal_map.items() if not present]

    return {
        "summary": (
            f"{source.name} was classified as {classification} with readiness score "
            f"{readiness_score:.3f} for {source.normalized_market_type()} adapter discovery."
        ),
        "source_kind": source.source_kind,
        "market_type": source.normalized_market_type(),
        "read_only_statement": "Discovery is descriptive only and cannot execute, route, submit, or manage trades.",
        "q_series_boundary": "Q Series remains the sole execution owner.",
        "required_umm_present": required_present,
        "required_umm_missing": required_missing,
        "signals_present": signals_present,
        "signals_missing": signals_missing,
        "field_count": len(fields),
        "sample_fields": list(fields[:40]),
        "warnings": list(evidence.warnings),
        "next_architecture_step": recommend_next_step(classification, evidence),
    }


def recommend_next_step(classification: str, evidence: AdapterDiscoveryEvidence) -> str:
    if classification == "adapter_ready":
        return "Register candidate with adapter registry after human review and compatibility validation."
    if classification == "adapter_candidate":
        return "Complete missing UMM fields and verify replay fixtures before registry promotion."
    if classification == "research_required":
        return "Gather schema, terms, rate limits, and health evidence before adapter work begins."
    return "Do not promote. Discovery evidence is insufficient for adapter design."


def build_telemetry(
    source: AdapterDiscoverySource,
    evidence: AdapterDiscoveryEvidence,
    readiness_score: float,
    classification: str,
    replay_key: str,
) -> Dict[str, Any]:
    return {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "architecture_role": ARCHITECTURE_ROLE,
        "market_type": source.normalized_market_type(),
        "source_id": source.source_id,
        "source_kind": source.source_kind,
        "classification": classification,
        "readiness_score": readiness_score,
        "warning_count": len(evidence.warnings),
        "required_umm_coverage_ratio": coverage_ratio(evidence.required_umm_coverage),
        "optional_umm_coverage_ratio": coverage_ratio(evidence.optional_umm_coverage),
        "market_specific_coverage_ratio": coverage_ratio(evidence.market_specific_coverage),
        "replay_key": replay_key,
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
    }


def coverage_ratio(coverage: Mapping[str, bool]) -> float:
    if not coverage:
        return 0.0
    return round(sum(1 for value in coverage.values() if value) / len(coverage), 6)


def discover_adapters(
    sources: Iterable[AdapterDiscoverySource],
    market_scope: Optional[Iterable[str]] = None,
    discovered_at: Optional[float] = None,
) -> AdapterDiscoverySnapshot:
    normalized_scope = tuple(
        sorted(
            normalize_market_type(market)
            for market in (market_scope if market_scope is not None else SUPPORTED_MARKETS)
        )
    )

    timestamp = float(discovered_at if discovered_at is not None else time.time())

    results: List[AdapterDiscoveryResult] = []
    for source in sources:
        if source.normalized_market_type() not in normalized_scope:
            continue
        results.append(discover_source(source, discovered_at=timestamp))

    results.sort(
        key=lambda result: (
            -result.readiness_score,
            result.source.normalized_market_type(),
            result.source.name.lower(),
            result.source.source_id,
        )
    )

    architecture = architecture_contract()

    replay_hash = stable_hash(
        {
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "created_at": timestamp,
            "market_scope": normalized_scope,
            "result_replay_keys": [result.replay_key for result in results],
            "architecture": architecture,
        }
    )

    return AdapterDiscoverySnapshot(
        engine_id=ENGINE_ID,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        created_at=timestamp,
        market_scope=normalized_scope,
        result_count=len(results),
        results=tuple(results),
        architecture=architecture,
        replay_hash=replay_hash,
    )

def architecture_contract() -> Dict[str, Any]:
    return {
        "oracle_mode": "read_only",
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
        "universal_market_model": True,
        "single_oracle_instance": True,
        "adapter_based_expansion": True,
        "event_driven_intelligence": True,
        "explainability_by_default": True,
        "replayability_by_default": True,
        "historical_memory_ready": True,
        "institutional_telemetry": True,
        "strategy_agnostic_q_series": True,
        "architecture_registry_ready": True,
        "architecture_manual_ready": True,
        "guardrails": list(READ_ONLY_GUARDRAILS),
    }


def snapshot_to_json(snapshot: AdapterDiscoverySnapshot, indent: int = 2) -> str:
    return json.dumps(snapshot.to_dict(), indent=indent, sort_keys=True, default=str)


def load_sources_from_json(path: str | Path) -> Tuple[AdapterDiscoverySource, ...]:
    file_path = Path(path)
    payload = json.loads(file_path.read_text(encoding="utf-8"))

    if isinstance(payload, Mapping):
        records = payload.get("sources", [])
    else:
        records = payload

    if not isinstance(records, list):
        raise ValueError("Discovery source JSON must be a list or an object with a 'sources' list.")

    return tuple(source_from_mapping(record) for record in records)


def source_from_mapping(record: Mapping[str, Any]) -> AdapterDiscoverySource:
    sample_payload = record.get("sample_payload")
    if sample_payload is not None and not isinstance(sample_payload, Mapping):
        raise ValueError("sample_payload must be a mapping when provided.")

    return AdapterDiscoverySource(
        source_id=str(record.get("source_id", "")).strip(),
        name=str(record.get("name", "")).strip(),
        market_type=str(record.get("market_type", "")).strip(),
        source_kind=str(record.get("source_kind", "unknown")).strip(),
        endpoint=optional_text(record.get("endpoint")),
        documentation_url=optional_text(record.get("documentation_url")),
        owner=optional_text(record.get("owner")),
        schema_fields=tuple(str(item).strip() for item in record.get("schema_fields", []) if str(item).strip()),
        sample_payload=sample_payload,
        rate_limit=optional_text(record.get("rate_limit")),
        terms_status=optional_text(record.get("terms_status")),
        historical_available=bool(record.get("historical_available", False)),
        health_probe=optional_text(record.get("health_probe")),
        enabled=bool(record.get("enabled", True)),
        notes=tuple(str(item).strip() for item in record.get("notes", []) if str(item).strip()),
    )


def optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class UniversalMarketAdapterDiscoveryEngine:
    """
    Stateful facade for OI-176 discovery operations.

    The class keeps an in-memory history of replayable discovery snapshots.
    It does not connect to external services, does not execute trades, and does
    not mutate any source system.
    """

    def __init__(self, engine_id: str = ENGINE_ID, engine_version: str = ENGINE_VERSION) -> None:
        self.engine_id = engine_id
        self.engine_version = engine_version
        self._history: List[AdapterDiscoverySnapshot] = []

    def discover(
        self,
        sources: Iterable[AdapterDiscoverySource],
        market_scope: Optional[Iterable[str]] = None,
        discovered_at: Optional[float] = None,
    ) -> AdapterDiscoverySnapshot:
        snapshot = discover_adapters(
            sources=sources,
            market_scope=market_scope,
            discovered_at=discovered_at,
        )
        self._history.append(snapshot)
        return snapshot

    def discover_from_json(
        self,
        path: str | Path,
        market_scope: Optional[Iterable[str]] = None,
        discovered_at: Optional[float] = None,
    ) -> AdapterDiscoverySnapshot:
        return self.discover(
            sources=load_sources_from_json(path),
            market_scope=market_scope,
            discovered_at=discovered_at,
        )

    def latest_snapshot(self) -> Optional[AdapterDiscoverySnapshot]:
        if not self._history:
            return None
        return self._history[-1]

    def history(self) -> Tuple[AdapterDiscoverySnapshot, ...]:
        return tuple(self._history)

    def diagnostics(self) -> Dict[str, Any]:
        latest = self.latest_snapshot()
        return {
            "engine_id": self.engine_id,
            "engine_version": self.engine_version,
            "engine_name": ENGINE_NAME,
            "architecture_role": ARCHITECTURE_ROLE,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
            "supported_markets": list(SUPPORTED_MARKETS),
            "history_count": len(self._history),
            "latest_replay_hash": latest.replay_hash if latest else None,
            "latest_result_count": latest.result_count if latest else 0,
            "guardrails": list(READ_ONLY_GUARDRAILS),
        }


oracle_universal_market_adapter_discovery_engine = UniversalMarketAdapterDiscoveryEngine()
universal_market_adapter_discovery_engine = oracle_universal_market_adapter_discovery_engine


def demo_sources() -> Tuple[AdapterDiscoverySource, ...]:
    return (
        AdapterDiscoverySource(
            source_id="demo.kalshi.prediction_markets",
            name="Demo Prediction Market Source",
            market_type="prediction_markets",
            source_kind="api_schema",
            endpoint="read_only://prediction/demo/markets",
            documentation_url="read_only://docs/prediction/demo",
            owner="oracle_intelligence",
            schema_fields=(
                "market_id",
                "market_type",
                "title",
                "status",
                "timestamp",
                "event_id",
                "outcomes",
                "best_bid",
                "best_ask",
                "probability",
                "volume",
                "liquidity",
                "expiry",
                "settlement_source",
                "source_url",
            ),
            sample_payload={
                "market_id": "DEMO-MARKET",
                "market_type": "prediction_markets",
                "title": "Demo event",
                "status": "open",
                "timestamp": "2026-07-02T00:00:00Z",
                "event_id": "DEMO-EVENT",
                "outcomes": [{"name": "yes"}, {"name": "no"}],
                "best_bid": 48,
                "best_ask": 52,
                "probability": 0.50,
                "volume": 10000,
                "liquidity": 2500,
                "expiry": "2026-12-31T23:59:59Z",
                "settlement_source": "demo",
                "source_url": "read_only://source/demo",
            },
            rate_limit="documented",
            terms_status="approved_for_read_only_research",
            historical_available=True,
            health_probe="schema_validation",
            enabled=True,
            notes=("Demo fixture for replayable OI-176 tests.",),
        ),
        AdapterDiscoverySource(
            source_id="demo.crypto.partial",
            name="Demo Crypto Partial Source",
            market_type="crypto",
            source_kind="vendor_export",
            schema_fields=("symbol", "price", "timestamp", "volume"),
            sample_payload={
                "symbol": "BTCUSD",
                "price": 65000,
                "timestamp": "2026-07-02T00:00:00Z",
                "volume": 123456,
            },
            rate_limit=None,
            terms_status=None,
            historical_available=False,
            health_probe=None,
            enabled=True,
            notes=("Partial fixture expected to require research.",),
        ),
    )


if __name__ == "__main__":
    engine = UniversalMarketAdapterDiscoveryEngine()
    snapshot = engine.discover(demo_sources(), discovered_at=1760000000.0)
    print(snapshot_to_json(snapshot))
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_discovery_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterDiscoverySource,
    UniversalMarketAdapterDiscoveryEngine,
    architecture_contract,
    demo_sources,
    discover_adapters,
    snapshot_to_json,
)


def test_discovery_snapshot_core_contract():
    snapshot = discover_adapters(demo_sources(), discovered_at=1760000000.0)

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.result_count == 2
    assert snapshot.replay_hash
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER

    classifications = {result.source.source_id: result.classification for result in snapshot.results}
    assert classifications["demo.kalshi.prediction_markets"] in {"adapter_ready", "adapter_candidate"}
    assert classifications["demo.crypto.partial"] in {"research_required", "not_ready", "adapter_candidate"}


def test_read_only_guardrails_and_explainability():
    source = AdapterDiscoverySource(
        source_id="test.weather.discovery",
        name="Weather Discovery Fixture",
        market_type="weather",
        source_kind="registry_item",
        schema_fields=(
            "event_id",
            "market_id",
            "market_type",
            "title",
            "status",
            "timestamp",
            "settlement_source",
            "source_url",
        ),
        sample_payload={
            "event_id": "WX-001",
            "market_id": "WX-MKT-001",
            "market_type": "weather",
            "title": "Temperature threshold fixture",
            "status": "observed",
            "timestamp": "2026-07-02T00:00:00Z",
            "settlement_source": "official_weather_station",
            "source_url": "read_only://weather/source",
        },
        rate_limit="documented",
        terms_status="approved_for_read_only_research",
        historical_available=True,
        health_probe="fixture_validation",
    )

    snapshot = discover_adapters([source], discovered_at=1760000000.0)
    result = snapshot.results[0]

    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert "cannot execute" in result.explanation["read_only_statement"]
    assert result.replay_key
    assert result.readiness_score > 0.60


def test_engine_history_and_json_serialization():
    engine = UniversalMarketAdapterDiscoveryEngine()
    snapshot = engine.discover(demo_sources(), market_scope=["prediction_markets"], discovered_at=1760000000.0)

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1
    assert snapshot.result_count == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Discovery Engine" in text
    assert "read_only" in text


def test_architecture_contract_is_institutional():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["strategy_agnostic_q_series"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_discovery_snapshot_core_contract()
    test_read_only_guardrails_and_explainability()
    test_engine_history_and_json_serialization()
    test_architecture_contract_is_institutional()
    print("[PASS] OI-176 Universal Market Adapter Discovery Engine")
    print(discover_adapters(demo_sources(), discovered_at=1760000000.0).to_dict())
'''


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def update_init() -> None:
    INIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if INIT_PATH.exists():
        existing = INIT_PATH.read_text(encoding="utf-8")
    else:
        existing = ""

    export_line = (
        "from .universal_market_adapter_discovery_engine import "
        "UniversalMarketAdapterDiscoveryEngine, "
        "oracle_universal_market_adapter_discovery_engine, "
        "universal_market_adapter_discovery_engine\n"
    )

    all_line = '"UniversalMarketAdapterDiscoveryEngine",\n'

    if export_line not in existing:
        existing = existing.rstrip() + "\n" + export_line

    if "__all__" not in existing:
        existing += "\n__all__ = [\n"
        existing += '    "UniversalMarketAdapterDiscoveryEngine",\n'
        existing += '    "oracle_universal_market_adapter_discovery_engine",\n'
        existing += '    "universal_market_adapter_discovery_engine",\n'
        existing += "]\n"
    else:
        if '"UniversalMarketAdapterDiscoveryEngine"' not in existing:
            existing = existing.replace("__all__ = [", '__all__ = [\n    "UniversalMarketAdapterDiscoveryEngine",')
        if '"oracle_universal_market_adapter_discovery_engine"' not in existing:
            existing = existing.replace("__all__ = [", '__all__ = [\n    "oracle_universal_market_adapter_discovery_engine",')
        if '"universal_market_adapter_discovery_engine"' not in existing:
            existing = existing.replace("__all__ = [", '__all__ = [\n    "universal_market_adapter_discovery_engine",')

    INIT_PATH.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-176 INSTALLER")
    print(" Universal Market Adapter Discovery Engine")
    print("========================================")

    write_file(MODULE_PATH, MODULE_CODE)
    print(f"[OK] Wrote {MODULE_PATH}")

    write_file(TEST_PATH, TEST_CODE)
    print(f"[OK] Wrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print()
    print("[DONE] OI-176 installed")
    print()
    print("Run:")
    print("py test_oi_176_universal_market_adapter_discovery_engine.py")


if __name__ == "__main__":
    main()