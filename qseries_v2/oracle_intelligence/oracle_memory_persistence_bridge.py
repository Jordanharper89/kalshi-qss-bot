"""
OI-043 Oracle Memory Persistence Bridge

Connects:
- OI-041 Oracle Memory Engine
- OI-042 Oracle Persistent Memory Store

Purpose:
- Persist Oracle memory records automatically.
- Reload persisted memory after restart.
- Keep Oracle fully read-only from an execution perspective.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .oracle_memory_engine import oracle_memory_engine, OracleMemoryEngine
from .oracle_persistent_memory_store import oracle_persistent_memory_store, OraclePersistentMemoryStore


class OracleMemoryPersistenceBridge:
    module_name = "oi_043_oracle_memory_persistence_bridge"

    def __init__(
        self,
        memory_engine: Optional[OracleMemoryEngine] = None,
        memory_store: Optional[OraclePersistentMemoryStore] = None,
    ) -> None:
        self.memory_engine = memory_engine or oracle_memory_engine
        self.memory_store = memory_store or oracle_persistent_memory_store

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "engine": self.memory_engine.status(),
            "store": self.memory_store.status(),
        }

    def remember_and_persist(
        self,
        memory_type: str,
        title: str,
        summary: str,
        payload: Optional[Dict[str, Any]] = None,
        market_ticker: Optional[str] = None,
        confidence: float = 50.0,
        importance: float = 50.0,
        tags: Optional[List[str]] = None,
        source_module: str = "oracle",
    ) -> Dict[str, Any]:
        record = self.memory_engine.remember(
            memory_type=memory_type,
            title=title,
            summary=summary,
            payload=payload,
            market_ticker=market_ticker,
            confidence=confidence,
            importance=importance,
            tags=tags,
            source_module=source_module,
        )

        return self.memory_store.upsert(record)

    def persist_existing_engine_memory(self) -> Dict[str, Any]:
        records = self.memory_engine.recall(limit=100000)
        saved = 0

        for record in records:
            self.memory_store.upsert(record)
            saved += 1

        return {
            "status": "ok",
            "persisted": saved,
            "read_only": True,
        }

    def recall_persistent(
        self,
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        return self.memory_store.recall(
            memory_type=memory_type,
            market_ticker=market_ticker,
            tag=tag,
            limit=limit,
        )

    def hydrate_engine_from_store(
        self,
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 100000,
    ) -> Dict[str, Any]:
        records = self.memory_store.recall(
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
        )

        loaded = 0

        for record in records:
            self.memory_engine.remember(
                memory_type=record["memory_type"],
                title=record["title"],
                summary=record["summary"],
                payload=record.get("payload", {}),
                market_ticker=record.get("market_ticker"),
                confidence=record.get("confidence", 50.0),
                importance=record.get("importance", 50.0),
                tags=record.get("tags", []),
                source_module=record.get("source_module", "oracle_persistent_store"),
            )
            loaded += 1

        return {
            "status": "ok",
            "hydrated": loaded,
            "read_only": True,
        }

    def search_persistent_memory(self, text: str, limit: int = 25) -> List[Dict[str, Any]]:
        return self.memory_store.search_text(text=text, limit=limit)


oracle_memory_persistence_bridge = OracleMemoryPersistenceBridge()
