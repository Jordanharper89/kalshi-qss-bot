
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .macro_event_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    MacroEventDiscoveryCapability,
    MacroEventDiscoveryEngineContract,
    MacroEventDiscoveryFamily,
    MacroEventDiscoveryHealth,
    MacroEventDiscoveryRequest,
    MacroEventDiscoveryResult,
    MacroEventDiscoveryTelemetry,
)
from .macro_event_source_adapter import MacroEventSnapshot, MacroEventSourceAdapter

SCHEMA_VERSION = "MED-003"
ENGINE_ID = "oracle.discovery.macro_event"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(v: Any) -> Any:
    if isinstance(v, Mapping):
        return MappingProxyType({str(k): _freeze(x) for k, x in v.items()})
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, tuple):
        return tuple(_freeze(x) for x in v)
    return v


def _stable_text(v: Any) -> str:
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{k}:{_stable_text(x)}" for k, x in sorted(v.items())) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_stable_text(x) for x in v) + "]"
    return repr(v)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return prefix + "." + sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class MacroEventOpportunity:
    opportunity_id: str
    schema_version: str
    event_id: str
    title: str
    family: str
    region: str
    currency: str
    opportunity_type: str
    source_engine_id: str
    event_score: float
    impact_score: float
    market_relevance_score: float
    surprise_potential_score: float
    confidence: float
    universal_market: Mapping[str, Any]
    status: str
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "title": self.title,
            "family": self.family,
            "region": self.region,
            "currency": self.currency,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "event_score": self.event_score,
            "impact_score": self.impact_score,
            "market_relevance_score": self.market_relevance_score,
            "surprise_potential_score": self.surprise_potential_score,
            "confidence": self.confidence,
            "universal_market": dict(self.universal_market),
            "status": self.status,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class MacroEventDiscoveryEngine(MacroEventDiscoveryEngineContract):
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = True

    def __init__(
        self,
        source_snapshots: Optional[Sequence[MacroEventSnapshot]] = None,
        min_event_score: float = 0.55,
    ) -> None:
        self.source_snapshots = tuple(source_snapshots or ())
        self.min_event_score = float(min_event_score)

    def capabilities(self) -> MacroEventDiscoveryCapability:
        return MacroEventDiscoveryCapability(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
            source_name="macro_event_snapshot",
            supports_replay=True,
            deterministic=True,
            telemetry=True,
            read_only=True,
            metadata={
                "engine_schema_version": self.schema_version,
                "produces": "UniversalOpportunity-shaped macro event opportunities",
                "execution": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
            },
        )

    def health(self) -> MacroEventDiscoveryHealth:
        return MacroEventDiscoveryHealth(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"engine_schema_version": self.schema_version, "read_only": True},
        )

    def discover(self, request: MacroEventDiscoveryRequest | None = None) -> MacroEventDiscoveryResult:
        started_at = _utc_now_iso()
        snapshots = self._resolve_snapshots(request)

        opportunities = []
        rejected = 0

        for snapshot in snapshots:
            opp = self._build_opportunity(snapshot)
            if opp is None:
                rejected += 1
                continue
            opportunities.append(opp)

        opportunities = tuple(
            sorted(
                opportunities,
                key=lambda o: (-o.event_score, -o.confidence, o.event_id),
            )
        )

        request_id = request.request_id if request is not None else "macro.event.discovery.default"

        telemetry = MacroEventDiscoveryTelemetry(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=len(snapshots),
            events_seen=len({s.event_id for s in snapshots}),
            opportunities_emitted=len(opportunities),
            rejected_records=rejected,
            metadata={
                "engine_schema_version": self.schema_version,
                "min_event_score": self.min_event_score,
                "deterministic_sort": True,
                "read_only": True,
                "execution_allowed": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
            },
            read_only=True,
        )

        return MacroEventDiscoveryResult(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            status="passed" if opportunities else "empty",
            opportunities=opportunities,
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )

    def _resolve_snapshots(self, request: MacroEventDiscoveryRequest | None) -> Tuple[MacroEventSnapshot, ...]:
        if request is None:
            return tuple(self.source_snapshots)

        metadata = request.metadata or {}
        records = None
        for key in ("snapshots", "macro_snapshots", "macro_events", "records", "raw_records"):
            if key in metadata:
                records = metadata[key]
                break

        if records is None:
            return tuple(self.source_snapshots)

        record_tuple = tuple(records)
        if all(isinstance(r, MacroEventSnapshot) for r in record_tuple):
            return record_tuple

        adapter = MacroEventSourceAdapter(source_name=request.source_name)
        return adapter.normalize_batch(record_tuple).snapshots

    def _impact_score(self, impact: str) -> float:
        table = {"low": 0.25, "medium": 0.55, "high": 0.90, "critical": 1.0}
        return table.get(str(impact).lower(), 0.50)

    def _market_relevance_score(self, snapshot: MacroEventSnapshot) -> float:
        markets = set(snapshot.affected_markets)
        score = 0.15
        if "PREDICTION_MARKETS" in markets:
            score += 0.35
        if "RATES" in markets:
            score += 0.25
        if "EQUITIES" in markets:
            score += 0.15
        if "CRYPTO" in markets:
            score += 0.10
        return round(min(1.0, score), 6)

    def _surprise_potential_score(self, snapshot: MacroEventSnapshot) -> float:
        score = 0.30
        if snapshot.forecast:
            score += 0.25
        if snapshot.previous:
            score += 0.15
        if snapshot.family in {"inflation_event", "fed_event", "jobs_event", "economic_release"}:
            score += 0.20
        if snapshot.actual:
            score += 0.10
        return round(min(1.0, score), 6)

    def _to_universal_market(self, snapshot: MacroEventSnapshot) -> Mapping[str, Any]:
        return _freeze({
            "schema_family": "UMM",
            "market_type": "macro_event",
            "event_id": snapshot.event_id,
            "title": snapshot.title,
            "family": snapshot.family,
            "region": snapshot.region,
            "country": snapshot.country,
            "currency": snapshot.currency,
            "impact": snapshot.impact,
            "scheduled_at": snapshot.scheduled_at,
            "affected_markets": snapshot.affected_markets,
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

    def _build_opportunity(self, snapshot: MacroEventSnapshot) -> Optional[MacroEventOpportunity]:
        if not snapshot.event_id or not snapshot.title:
            return None

        impact_score = self._impact_score(snapshot.impact)
        market_score = self._market_relevance_score(snapshot)
        surprise_score = self._surprise_potential_score(snapshot)
        event_score = round(impact_score * 0.45 + market_score * 0.35 + surprise_score * 0.20, 6)

        if event_score < self.min_event_score:
            return None

        confidence = round(min(1.0, event_score * 0.75 + impact_score * 0.25), 6)

        identity = {
            "event_id": snapshot.event_id,
            "title": snapshot.title,
            "family": snapshot.family,
            "scheduled_at": snapshot.scheduled_at,
            "event_score": event_score,
        }

        explanation = MappingProxyType({
            "summary": "Macro event passed read-only impact, market relevance, and surprise-potential scoring.",
            "event_id": snapshot.event_id,
            "title": snapshot.title,
            "impact_score": impact_score,
            "market_relevance_score": market_score,
            "surprise_potential_score": surprise_score,
            "event_score": event_score,
            "rules": [
                "read_only_scan",
                "impact_score_guardrail",
                "market_relevance_guardrail",
                "surprise_potential_guardrail",
                "deterministic_opportunity_id",
                "no_execution_authority",
            ],
        })

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "source_engine_id": self.engine_id,
            "event_id": snapshot.event_id,
            "created_at": _utc_now_iso(),
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return MacroEventOpportunity(
            opportunity_id=_stable_id("uop.macro_event", identity),
            schema_version="UOM-compatible/MED-003",
            event_id=snapshot.event_id,
            title=snapshot.title,
            family=snapshot.family,
            region=snapshot.region,
            currency=snapshot.currency,
            opportunity_type="macro_event_signal",
            source_engine_id=self.engine_id,
            event_score=event_score,
            impact_score=impact_score,
            market_relevance_score=market_score,
            surprise_potential_score=surprise_score,
            confidence=confidence,
            universal_market=self._to_universal_market(snapshot),
            status="discovered",
            explanation=explanation,
            telemetry=telemetry,
            read_only=True,
        )


__all__ = ["SCHEMA_VERSION", "ENGINE_ID", "MacroEventOpportunity", "MacroEventDiscoveryEngine"]
