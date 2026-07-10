
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
