from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_certification_registry_engine.py"
TEST = ROOT / "test_oi_203_universal_market_adapter_replay_certification_registry_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
"""
OI-203 — Oracle Universal Market Adapter Replay Certification Registry Engine

Read-only Oracle Intelligence component.

Registers replay certification outputs from OI-201 into deterministic,
immutable, explainable registry records.

Duplicate identity is based on certification content, not list position.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Tuple


ENGINE_ID = "OI-203"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Certification Registry Engine"
ENGINE_VERSION = "1.0.1"


@dataclass(frozen=True)
class ReplayCertificationRegistryRecord:
    registry_id: str
    source_engine_id: str
    certified: bool
    certification_level: str
    status: str
    intelligence_score: float
    signal_count: int
    decision_count: int
    reason_codes: Tuple[str, ...] = field(default_factory=tuple)
    explanation: str = ""
    source: Dict[str, Any] = field(default_factory=dict)
    telemetry: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        return data


@dataclass(frozen=True)
class ReplayCertificationRegistryResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    registered_count: int
    rejected_count: int
    duplicate_count: int
    records: Tuple[ReplayCertificationRegistryRecord, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "registered_count": self.registered_count,
            "rejected_count": self.rejected_count,
            "duplicate_count": self.duplicate_count,
            "records": [record.to_dict() for record in self.records],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayCertificationRegistryEngine:
    def register(self, certifications: Any) -> ReplayCertificationRegistryResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        items = self._extract_items(certifications)

        records: List[ReplayCertificationRegistryRecord] = []
        seen_ids: set[str] = set()
        rejected_count = 0
        duplicate_count = 0

        for item in items:
            data = self._to_mapping(item)

            if not self._valid_certification(data):
                rejected_count += 1
                continue

            registry_id = self._registry_id(data)

            if registry_id in seen_ids:
                duplicate_count += 1
                continue

            seen_ids.add(registry_id)

            decisions = self._extract_decisions(data)
            reason_codes = self._collect_reason_codes(decisions)

            records.append(
                ReplayCertificationRegistryRecord(
                    registry_id=registry_id,
                    source_engine_id=str(data.get("engine_id", "unknown")),
                    certified=bool(data.get("certified", False)),
                    certification_level=str(data.get("certification_level", "unknown")),
                    status=str(data.get("status", "unknown")),
                    intelligence_score=self._clamp01(self._number(data, "intelligence_score", default=0.0)),
                    signal_count=int(self._number(data, "signal_count", default=0.0)),
                    decision_count=len(decisions),
                    reason_codes=tuple(reason_codes),
                    explanation=str(data.get("explanation", "")),
                    source=dict(data),
                    telemetry={
                        "engine_id": ENGINE_ID,
                        "read_only": True,
                        "oracle_role": "brain",
                        "execution_owner": "Q Series",
                        "source_engine_id": data.get("engine_id"),
                        "registry_is_immutable": True,
                        "certification_is_advisory": True,
                    },
                )
            )

        if records and rejected_count == 0:
            status = "ok"
        elif records:
            status = "review"
        else:
            status = "empty"

        return ReplayCertificationRegistryResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            registered_count=len(records),
            rejected_count=rejected_count,
            duplicate_count=duplicate_count,
            records=tuple(records),
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "read_only": True,
                "oracle_role": "brain",
                "execution_owner": "Q Series",
                "does_not_execute": True,
                "does_not_route_orders": True,
                "does_not_manage_positions": True,
                "canonical_input": "ReplayRankingCertificationResult compatible",
                "canonical_output": "ReplayCertificationRegistryResult",
                "registry_is_advisory": True,
                "duplicate_identity": "content_hash",
                "registered_count": len(records),
                "rejected_count": rejected_count,
                "duplicate_count": duplicate_count,
                "explainability": True,
                "replayability": True,
            },
            explanation=(
                f"Registered {len(records)} replay certification record(s), rejected "
                f"{rejected_count}, ignored {duplicate_count} duplicate(s). Oracle registry "
                "is read-only and advisory; Q Series remains the only execution engine."
            ),
        )

    def _extract_items(self, certifications: Any) -> List[Any]:
        if certifications is None:
            return []
        if isinstance(certifications, Mapping):
            if "records" in certifications:
                return list(certifications.get("records") or [])
            return [certifications]
        if isinstance(certifications, Iterable) and not isinstance(certifications, (str, bytes)):
            return list(certifications)
        return [certifications]

    def _valid_certification(self, data: Mapping[str, Any]) -> bool:
        required = {"engine_id", "status", "certified", "certification_level", "intelligence_score"}
        return bool(data) and required.issubset(set(data.keys()))

    def _extract_decisions(self, data: Mapping[str, Any]) -> List[Dict[str, Any]]:
        raw = data.get("decisions", [])
        if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
            return []
        output: List[Dict[str, Any]] = []
        for item in raw:
            mapped = self._to_mapping(item)
            if mapped:
                output.append(mapped)
        return output

    def _collect_reason_codes(self, decisions: List[Mapping[str, Any]]) -> List[str]:
        codes: List[str] = []
        for decision in decisions:
            raw = decision.get("reason_codes", [])
            if isinstance(raw, str):
                raw = [raw]
            if isinstance(raw, Iterable):
                for code in raw:
                    code_text = str(code).strip()
                    if code_text and code_text not in codes:
                        codes.append(code_text)
        return codes

    def _registry_id(self, data: Mapping[str, Any]) -> str:
        stable = {
            "engine_id": data.get("engine_id"),
            "status": data.get("status"),
            "certified": data.get("certified"),
            "certification_level": data.get("certification_level"),
            "intelligence_score": data.get("intelligence_score"),
            "signal_count": data.get("signal_count"),
            "decisions": data.get("decisions"),
            "explanation": data.get("explanation"),
        }
        digest = sha256(repr(stable).encode("utf-8")).hexdigest()[:16]
        return f"replay_cert_registry_{digest}"

    def _to_mapping(self, item: Any) -> Dict[str, Any]:
        if item is None:
            return {}
        if isinstance(item, Mapping):
            return dict(item)
        if hasattr(item, "to_dict") and callable(item.to_dict):
            mapped = item.to_dict()
            if isinstance(mapped, Mapping):
                return dict(mapped)
        if hasattr(item, "__dict__"):
            return dict(vars(item))
        return {}

    def _number(self, data: Mapping[str, Any], key: str, *, default: float = 0.0) -> float:
        try:
            return float(data.get(key, default))
        except (TypeError, ValueError):
            return float(default)

    def _clamp01(self, value: float) -> float:
        value = float(value)
        if value > 1.0 and value <= 100.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))


def register_replay_certifications(certifications: Any) -> ReplayCertificationRegistryResult:
    return UniversalMarketAdapterReplayCertificationRegistryEngine().register(certifications)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayCertificationRegistryRecord",
    "ReplayCertificationRegistryResult",
    "UniversalMarketAdapterReplayCertificationRegistryEngine",
    "register_replay_certifications",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryEngine,
    register_replay_certifications,
)


def sample_certification():
    return {
        "engine_id": "OI-201",
        "status": "certified",
        "certified": True,
        "certification_level": "certified",
        "intelligence_score": 0.64,
        "signal_count": 1,
        "decisions": [
            {
                "decision_id": "D1",
                "certified": True,
                "certification_level": "certified",
                "confidence": 0.64,
                "reason_codes": [
                    "READ_ONLY_ORACLE_CERTIFICATION",
                    "Q_SERIES_EXECUTION_REQUIRED",
                    "PASSING_INTELLIGENCE_SCORE",
                ],
            }
        ],
        "telemetry": {"read_only": True, "execution_owner": "Q Series"},
        "explanation": "Demo certification.",
    }


def test_registers_valid_certification():
    result = UniversalMarketAdapterReplayCertificationRegistryEngine().register(sample_certification())

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.registered_count == 1
    assert result.rejected_count == 0
    assert result.duplicate_count == 0
    assert result.records[0].source_engine_id == "OI-201"
    assert result.records[0].certified is True
    assert result.records[0].certification_level == "certified"
    assert "READ_ONLY_ORACLE_CERTIFICATION" in result.records[0].reason_codes
    assert "Q_SERIES_EXECUTION_REQUIRED" in result.records[0].reason_codes
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True


def test_duplicate_certifications_are_ignored():
    cert = sample_certification()
    result = register_replay_certifications([cert, cert])

    assert result.registered_count == 1
    assert result.duplicate_count == 1
    assert result.rejected_count == 0


def test_distinct_certifications_both_register():
    cert_one = sample_certification()
    cert_two = sample_certification()
    cert_two["intelligence_score"] = 0.82
    cert_two["certification_level"] = "strong_certified"

    result = register_replay_certifications([cert_one, cert_two])

    assert result.registered_count == 2
    assert result.duplicate_count == 0
    assert result.rejected_count == 0
    assert result.records[0].registry_id != result.records[1].registry_id


def test_invalid_certification_is_rejected_safely():
    result = register_replay_certifications([{"engine_id": "BAD"}])

    assert result.status == "empty"
    assert result.registered_count == 0
    assert result.rejected_count == 1
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_registers_valid_certification()
    test_duplicate_certifications_are_ignored()
    test_distinct_certifications_both_register()
    test_invalid_certification_is_rejected_safely()

    print("[PASS] OI-203 Universal Market Adapter Replay Certification Registry Engine")
    print(register_replay_certifications(sample_certification()).to_dict())
'''


def ensure_package() -> None:
    PKG.mkdir(parents=True, exist_ok=True)
    if not INIT.exists():
        INIT.write_text("", encoding="utf-8")


def update_init() -> None:
    export_line = (
        "from .universal_market_adapter_replay_certification_registry_engine import "
        "UniversalMarketAdapterReplayCertificationRegistryEngine, "
        "register_replay_certifications\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-203 INSTALLER")
    print(" Universal Market Adapter Replay Certification Registry Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-203 installed")
    print()
    print("Run:")
    print("py test_oi_203_universal_market_adapter_replay_certification_registry_engine.py")


if __name__ == "__main__":
    main()