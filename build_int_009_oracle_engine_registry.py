from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "integration" / "oracle_engine_registry.py"
TEST = ROOT / "test_int_009_oracle_engine_registry.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleIntelligenceEngineContract,
    OracleIntelligenceContractValidator,
)


@dataclass(frozen=True)
class OracleEngineRegistryEntry:
    engine_id: str
    name: str
    version: str
    description: str
    capabilities: List[Dict[str, Any]]
    schema: Dict[str, Any]
    health: Dict[str, Any]
    registered_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleEngineRegistry:
    """
    INT-009 Oracle Engine Registry.

    Canonical registry for read-only Oracle Intelligence engines.
    """

    def __init__(self) -> None:
        self._engines: Dict[str, OracleIntelligenceEngineContract] = {}
        self._entries: Dict[str, OracleEngineRegistryEntry] = {}

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def register(self, engine: OracleIntelligenceEngineContract) -> OracleEngineRegistryEntry:
        validation = OracleIntelligenceContractValidator.validate(engine)
        if validation["status"] != "ok":
            raise ValueError(f"engine does not satisfy Oracle contract: {validation['missing_methods']}")

        metadata = engine.metadata()
        if not metadata.oracle_read_only:
            raise ValueError("oracle engine must be read-only")

        entry = OracleEngineRegistryEntry(
            engine_id=metadata.engine_id,
            name=metadata.name,
            version=metadata.version,
            description=metadata.description,
            capabilities=[cap.to_dict() for cap in engine.capabilities()],
            schema=engine.schema(),
            health=engine.health().to_dict(),
            registered_at=self.now_iso(),
        )

        self._engines[metadata.engine_id] = engine
        self._entries[metadata.engine_id] = entry
        return entry

    def unregister(self, engine_id: str) -> bool:
        existed = engine_id in self._engines
        self._engines.pop(engine_id, None)
        self._entries.pop(engine_id, None)
        return existed

    def get_engine(self, engine_id: str) -> Optional[OracleIntelligenceEngineContract]:
        return self._engines.get(engine_id)

    def get_entry(self, engine_id: str) -> Optional[OracleEngineRegistryEntry]:
        return self._entries.get(engine_id)

    def list_entries(self) -> List[OracleEngineRegistryEntry]:
        return [self._entries[key] for key in sorted(self._entries.keys())]

    def list_engines(self) -> List[OracleIntelligenceEngineContract]:
        return [self._engines[key] for key in sorted(self._engines.keys())]

    def refresh_health(self) -> Dict[str, Dict[str, Any]]:
        health_map: Dict[str, Dict[str, Any]] = {}

        for engine_id, engine in self._engines.items():
            health_map[engine_id] = engine.health().to_dict()

        return health_map

    def count(self) -> int:
        return len(self._engines)

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "registry": "oracle_engine_registry",
            "engine_count": self.count(),
            "engines": [entry.to_dict() for entry in self.list_entries()],
        }


def create_oracle_engine_registry() -> OracleEngineRegistry:
    return OracleEngineRegistry()


oracle_engine_registry = create_oracle_engine_registry


__all__ = [
    "OracleEngineRegistryEntry",
    "OracleEngineRegistry",
    "create_oracle_engine_registry",
    "oracle_engine_registry",
]
'''

test_code = r'''
from datetime import datetime, timezone

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionResult,
    OraclePredictionRequest,
    OracleExplanation,
    OracleEngineHealth,
)
from qseries_v2.integration.oracle_engine_registry import (
    OracleEngineRegistry,
    create_oracle_engine_registry,
    oracle_engine_registry,
)


class RegistryDummyEngine:
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.registry.test",
            name="Registry Test Engine",
            version="1.0.0",
            description="Registry test engine",
            oracle_read_only=True,
        )

    def capabilities(self):
        return [
            OracleEngineCapability(
                name="predict_market",
                description="Predict market",
                inputs=["market_id"],
                outputs=["prediction"],
            )
        ]

    def schema(self):
        return {"request": ["market_id"], "response": ["prediction"]}

    def health(self):
        return OracleEngineHealth(
            engine_id="oracle.registry.test",
            status="ok",
            details={"ready": True},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request):
        return OraclePredictionResult(
            engine_id="oracle.registry.test",
            market_id=request.market_id,
            prediction="YES",
            confidence=0.80,
            score=0.08,
            features={},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request):
        return OracleExplanation(
            engine_id="oracle.registry.test",
            market_id=request.market_id,
            summary="Registry test explanation",
            reasons=["test"],
            evidence={},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


class UnsafeEngine(RegistryDummyEngine):
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.unsafe",
            name="Unsafe Engine",
            version="1.0.0",
            description="Unsafe",
            oracle_read_only=False,
        )


def test_int_009_oracle_engine_registry():
    registry = create_oracle_engine_registry()

    assert isinstance(registry, OracleEngineRegistry)
    assert oracle_engine_registry is create_oracle_engine_registry

    entry = registry.register(RegistryDummyEngine())

    assert entry.engine_id == "oracle.registry.test"
    assert registry.count() == 1
    assert registry.get_engine("oracle.registry.test") is not None
    assert registry.get_entry("oracle.registry.test") == entry
    assert len(registry.list_entries()) == 1
    assert len(registry.list_engines()) == 1

    health_map = registry.refresh_health()
    assert health_map["oracle.registry.test"]["status"] == "ok"

    health = registry.health()
    assert health["status"] == "ok"
    assert health["engine_count"] == 1

    try:
        registry.register(UnsafeEngine())
        assert False, "unsafe engine should fail"
    except ValueError as exc:
        assert "read-only" in str(exc)

    assert registry.unregister("oracle.registry.test") is True
    assert registry.count() == 0
    assert registry.unregister("missing") is False

    print("[PASS] INT-009 Oracle Engine Registry")
    print(health)


if __name__ == "__main__":
    test_int_009_oracle_engine_registry()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "integration" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .oracle_engine_registry import "
    "OracleEngineRegistryEntry, OracleEngineRegistry, "
    "create_oracle_engine_registry, oracle_engine_registry\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" INT-009 INSTALLER")
print(" Oracle Engine Registry")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] INT-009 installed")
print("")
print("Run:")
print("py test_int_009_oracle_engine_registry.py")