from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "news_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_FILE = MODULE_DIR / "news_intelligence_discovery_replay_ledger.py"
TEST_FILE = ROOT / "test_nid_008_news_intelligence_discovery_replay_ledger.py"
INIT_FILE = MODULE_DIR / "__init__.py"

LEDGER_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .news_intelligence_discovery_oos_runtime_gate import NewsIntelligenceDiscoveryOOSRuntimeGate

SCHEMA_VERSION = "NID-008"
LEDGER_ID = "oracle.discovery.ledger.news_intelligence_replay"
VOLATILE_KEYS = {"created_at", "checked_at", "started_at", "completed_at", "run_at", "timestamp"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_volatile(v: Any) -> Any:
    if isinstance(v, Mapping):
        return {str(k): _strip_volatile(x) for k, x in v.items() if str(k) not in VOLATILE_KEYS}
    if isinstance(v, list):
        return [_strip_volatile(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_strip_volatile(x) for x in v)
    return v


def _stable_text(v: Any) -> str:
    v = _strip_volatile(v)
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{str(k)}:{_stable_text(x)}" for k, x in sorted(v.items(), key=lambda i: str(i[0]))) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_stable_text(x) for x in v) + "]"
    return repr(v)


def _fingerprint(v: Any) -> str:
    return sha256(_stable_text(v).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NewsIntelligenceReplayLedgerEntry:
    schema_version: str
    ledger_id: str
    entry_id: str
    packet_id: str
    opportunity_id: str
    article_id: str
    title: str
    registry_key: str
    packet_fingerprint: str
    payload_fingerprint: str
    audit_fingerprint: str
    replay_status: str
    payload_summary: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "entry_id": self.entry_id,
            "packet_id": self.packet_id,
            "opportunity_id": self.opportunity_id,
            "article_id": self.article_id,
            "title": self.title,
            "registry_key": self.registry_key,
            "packet_fingerprint": self.packet_fingerprint,
            "payload_fingerprint": self.payload_fingerprint,
            "audit_fingerprint": self.audit_fingerprint,
            "replay_status": self.replay_status,
            "payload_summary": dict(self.payload_summary),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class NewsIntelligenceReplayLedgerReport:
    schema_version: str
    ledger_id: str
    status: str
    entries: Tuple[NewsIntelligenceReplayLedgerEntry, ...]
    run_fingerprint: str
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "status": self.status,
            "entries": [e.to_dict() for e in self.entries],
            "run_fingerprint": self.run_fingerprint,
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class NewsIntelligenceReplayComparisonReport:
    schema_version: str
    ledger_id: str
    status: str
    matching: bool
    baseline_fingerprint: str
    replay_fingerprint: str
    baseline_entries: int
    replay_entries: int
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "status": self.status,
            "matching": self.matching,
            "baseline_fingerprint": self.baseline_fingerprint,
            "replay_fingerprint": self.replay_fingerprint,
            "baseline_entries": self.baseline_entries,
            "replay_entries": self.replay_entries,
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class NewsIntelligenceDiscoveryReplayLedger:
    schema_version = SCHEMA_VERSION
    ledger_id = LEDGER_ID
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "read_only": True,
            "accepts": "NID-007 OOS runtime packets",
            "emits": "immutable news intelligence replay ledger entries",
            "supports_replay_comparison": True,
            "deterministic": True,
            "canonicalizes_volatile_fields": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def record_packets(self, packets: Sequence[Any]) -> NewsIntelligenceReplayLedgerReport:
        started_at = _utc_now_iso()
        packet_tuple = tuple(packets or ())
        entries = tuple(sorted((self._entry_from_packet(p) for p in packet_tuple), key=lambda e: (e.registry_key, e.packet_id)))

        run_fingerprint = _fingerprint(tuple({
            "entry_id": e.entry_id,
            "packet_id": e.packet_id,
            "opportunity_id": e.opportunity_id,
            "article_id": e.article_id,
            "registry_key": e.registry_key,
            "packet_fingerprint": e.packet_fingerprint,
            "payload_fingerprint": e.payload_fingerprint,
            "audit_fingerprint": e.audit_fingerprint,
        } for e in entries))

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "packets_seen": len(packet_tuple),
            "entries_emitted": len(entries),
            "run_fingerprint": run_fingerprint,
            "read_only": True,
            "deterministic_sort": True,
            "volatile_fields_excluded": sorted(VOLATILE_KEYS),
        })

        return NewsIntelligenceReplayLedgerReport(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            status="passed" if entries else "empty",
            entries=entries,
            run_fingerprint=run_fingerprint,
            telemetry=telemetry,
            read_only=True,
        )

    def run_discovery_and_record(
        self,
        raw_records: Sequence[Any] | None = None,
        source_name: str = "news_intelligence_replay_ledger_source",
        min_news_score: float = 0.55,
    ) -> NewsIntelligenceReplayLedgerReport:
        gate = NewsIntelligenceDiscoveryOOSRuntimeGate(source_name=source_name, min_news_score=min_news_score)
        return self.record_packets(gate.run(raw_records).packets)

    def compare(self, baseline: NewsIntelligenceReplayLedgerReport, replay: NewsIntelligenceReplayLedgerReport) -> NewsIntelligenceReplayComparisonReport:
        started_at = _utc_now_iso()
        matching = baseline.run_fingerprint == replay.run_fingerprint and len(baseline.entries) == len(replay.entries)
        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "baseline_entries": len(baseline.entries),
            "replay_entries": len(replay.entries),
            "read_only": True,
        })
        return NewsIntelligenceReplayComparisonReport(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            status="matched" if matching else "mismatch",
            matching=matching,
            baseline_fingerprint=baseline.run_fingerprint,
            replay_fingerprint=replay.run_fingerprint,
            baseline_entries=len(baseline.entries),
            replay_entries=len(replay.entries),
            telemetry=telemetry,
            read_only=True,
        )

    def _entry_from_packet(self, packet: Any) -> NewsIntelligenceReplayLedgerEntry:
        payload = dict(getattr(packet, "payload", {}) or {})
        audit = dict(getattr(packet, "audit", {}) or {})
        canonical_payload = _strip_volatile(payload)
        canonical_audit = _strip_volatile(audit)

        packet_payload = {
            "packet_id": getattr(packet, "packet_id", None),
            "registry_key": getattr(packet, "registry_key", None),
            "opportunity_id": getattr(packet, "opportunity_id", None),
            "article_id": getattr(packet, "article_id", None),
            "title": getattr(packet, "title", None),
            "pipeline_status": getattr(packet, "pipeline_status", None),
            "payload": canonical_payload,
            "audit": canonical_audit,
            "read_only": getattr(packet, "read_only", None),
        }

        payload_summary = MappingProxyType({
            "opportunity_type": canonical_payload.get("opportunity_type"),
            "source_engine_id": canonical_payload.get("source_engine_id"),
            "validation_required": canonical_payload.get("validation_required"),
            "ranking_required": canonical_payload.get("ranking_required"),
            "registry_required": canonical_payload.get("registry_required"),
            "execution_allowed": canonical_payload.get("execution_allowed"),
            "order_allowed": canonical_payload.get("order_allowed"),
            "position_sizing_allowed": canonical_payload.get("position_sizing_allowed"),
            "read_only": canonical_payload.get("read_only"),
        })

        packet_fingerprint = _fingerprint(packet_payload)

        return NewsIntelligenceReplayLedgerEntry(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            entry_id=f"replay.entry:{packet_fingerprint[:24]}",
            packet_id=str(packet_payload["packet_id"]),
            opportunity_id=str(packet_payload["opportunity_id"]),
            article_id=str(packet_payload["article_id"]),
            title=str(packet_payload["title"]),
            registry_key=str(packet_payload["registry_key"]),
            packet_fingerprint=packet_fingerprint,
            payload_fingerprint=_fingerprint(canonical_payload),
            audit_fingerprint=_fingerprint(canonical_audit),
            replay_status="recorded",
            payload_summary=payload_summary,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "LEDGER_ID",
    "NewsIntelligenceReplayLedgerEntry",
    "NewsIntelligenceReplayLedgerReport",
    "NewsIntelligenceReplayComparisonReport",
    "NewsIntelligenceDiscoveryReplayLedger",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_replay_ledger import (
    NewsIntelligenceDiscoveryReplayLedger,
)


def test_nid_008_news_intelligence_discovery_replay_ledger():
    raw = [
        {"article_id": "article_b", "headline": "Fed signals slower cuts after inflation surprise", "publisher": "MarketWire", "link": "https://example.test/fed", "time": "2026-01-15T14:00:00Z", "category": "fed", "sentiment": "hawkish", "importance": "high", "relevance": 0.91, "markets": "RATES, EQUITIES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
        {"id": "article_a", "title": "CPI comes in hotter than expected", "source": "EconomicDesk", "url": "https://example.test/cpi", "published_at": "2026-01-15T13:30:00Z", "topic": "inflation", "sentiment": "negative", "impact": "high", "relevance_score": 0.95, "affected_markets": ["RATES", "PREDICTION_MARKETS"], "entities": ["CPI", "USD"]},
        {"article_id": "article_minor", "title": "Local market commentary", "source": "SmallWire", "published_at": "2026-01-15T12:00:00Z", "topic": "local", "impact": "low", "relevance_score": 0.20, "affected_markets": ["LOCAL"]},
    ]

    ledger = NewsIntelligenceDiscoveryReplayLedger()
    caps = ledger.capabilities()
    health = ledger.health()

    baseline = ledger.run_discovery_and_record(raw, source_name="nid_008_test_source", min_news_score=0.55)
    replay = ledger.run_discovery_and_record(list(reversed(raw)), source_name="nid_008_test_source", min_news_score=0.55)
    comparison = ledger.compare(baseline, replay)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["deterministic"] is True
    assert caps["canonicalizes_volatile_fields"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert baseline.schema_version == "NID-008"
    assert baseline.ledger_id == "oracle.discovery.ledger.news_intelligence_replay"
    assert baseline.status == "passed"
    assert baseline.read_only is True
    assert len(baseline.entries) == 2

    assert baseline.run_fingerprint == replay.run_fingerprint
    assert comparison.matching is True
    assert comparison.status == "matched"

    first = baseline.entries[0]
    assert first.read_only is True
    assert first.replay_status == "recorded"
    assert first.packet_fingerprint
    assert first.payload_fingerprint
    assert first.audit_fingerprint
    assert first.payload_summary["validation_required"] is True
    assert first.payload_summary["ranking_required"] is True
    assert first.payload_summary["registry_required"] is True
    assert first.payload_summary["execution_allowed"] is False
    assert first.payload_summary["order_allowed"] is False
    assert first.payload_summary["position_sizing_allowed"] is False
    assert first.payload_summary["read_only"] is True

    try:
        first.payload_summary["execution_allowed"] = True
        raise AssertionError("payload summary should be immutable")
    except TypeError:
        pass

    d = baseline.to_dict()
    c = comparison.to_dict()
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["entries_emitted"] == 2
    assert "created_at" in d["telemetry"]["volatile_fields_excluded"]
    assert c["matching"] is True
    assert c["baseline_entries"] == 2
    assert c["replay_entries"] == 2

    print("[PASS] NID-008 News Intelligence Discovery Replay Ledger")
    print({
        "schema_version": d["schema_version"],
        "ledger_id": d["ledger_id"],
        "status": d["status"],
        "entries": len(d["entries"]),
        "replay_match": c["matching"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_008_news_intelligence_discovery_replay_ledger()
'''

INIT_EXPORT = '''
try:
    from .news_intelligence_discovery_replay_ledger import (
        NewsIntelligenceDiscoveryReplayLedger,
        NewsIntelligenceReplayLedgerEntry,
        NewsIntelligenceReplayLedgerReport,
        NewsIntelligenceReplayComparisonReport,
    )
except Exception:
    pass
'''

LEDGER_FILE.write_text(LEDGER_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "NewsIntelligenceDiscoveryReplayLedger" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" NID-008 INSTALLER")
print(" News Intelligence Discovery Replay Ledger")
print("========================================")
print(f"[OK] Wrote {LEDGER_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] NID-008 installed")
print()
print("Run:")
print("py test_nid_008_news_intelligence_discovery_replay_ledger.py")