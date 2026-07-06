from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "oracle_knowledge_graph.py"
TEST = ROOT / "test_oi_050_oracle_knowledge_graph.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-050 Oracle Knowledge Graph

Connects Oracle memory into a structured intelligence graph.

Nodes:
- market
- memory
- pattern
- regime
- strategy
- category
- forecast
- outcome
- tag

Edges:
- HAS_MEMORY
- HAS_PATTERN
- IN_REGIME
- USES_STRATEGY
- IN_CATEGORY
- FORECASTED
- RESOLVED_AS
- TAGGED
- SIMILAR_TO

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set, Tuple

from .oracle_memory_persistence_bridge import (
    oracle_memory_persistence_bridge,
    OracleMemoryPersistenceBridge,
)


@dataclass
class KnowledgeNode:
    node_id: str
    node_type: str
    label: str
    properties: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeEdge:
    edge_id: str
    source: str
    target: str
    relation: str
    weight: float
    properties: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleKnowledgeGraph:
    module_name = "oi_050_oracle_knowledge_graph"

    def __init__(self, memory_bridge: Optional[OracleMemoryPersistenceBridge] = None) -> None:
        self.memory_bridge = memory_bridge or oracle_memory_persistence_bridge
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        self.out_edges: Dict[str, List[str]] = defaultdict(list)
        self.in_edges: Dict[str, List[str]] = defaultdict(list)

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "memory_bridge": self.memory_bridge.status()["status"],
        }

    def build_from_memory(
        self,
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 10000,
        clear_existing: bool = True,
    ) -> Dict[str, Any]:
        if clear_existing:
            self.clear()

        records = self.memory_bridge.recall_persistent(
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
        )

        for record in records:
            self._ingest_memory_record(record)

        return {
            "status": "ok",
            "read_only": True,
            "records_ingested": len(records),
            "nodes": len(self.nodes),
            "edges": len(self.edges),
        }

    def clear(self) -> None:
        self.nodes.clear()
        self.edges.clear()
        self.out_edges.clear()
        self.in_edges.clear()

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        node = self.nodes.get(node_id)
        return node.to_dict() if node else None

    def neighbors(
        self,
        node_id: str,
        relation: Optional[str] = None,
        direction: str = "both",
        limit: int = 50,
    ) -> Dict[str, Any]:
        edge_ids = []

        if direction in {"out", "both"}:
            edge_ids.extend(self.out_edges.get(node_id, []))

        if direction in {"in", "both"}:
            edge_ids.extend(self.in_edges.get(node_id, []))

        results = []

        for edge_id in edge_ids:
            edge = self.edges[edge_id]

            if relation and edge.relation != relation:
                continue

            other_id = edge.target if edge.source == node_id else edge.source
            node = self.nodes.get(other_id)

            if node:
                results.append({
                    "node": node.to_dict(),
                    "edge": edge.to_dict(),
                })

        results.sort(key=lambda x: x["edge"]["weight"], reverse=True)

        return {
            "status": "ok",
            "read_only": True,
            "node_id": node_id,
            "neighbors": results[:limit],
        }

    def find_nodes(
        self,
        node_type: Optional[str] = None,
        text: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        results = []

        for node in self.nodes.values():
            if node_type and node.node_type != node_type:
                continue

            if text:
                haystack = f"{node.node_id} {node.label} {node.properties}".lower()
                if text.lower() not in haystack:
                    continue

            results.append(node.to_dict())

        results.sort(key=lambda n: n["label"])
        return results[:limit]

    def path_between(
        self,
        source: str,
        target: str,
        max_depth: int = 4,
    ) -> Dict[str, Any]:
        if source not in self.nodes or target not in self.nodes:
            return {
                "status": "not_found",
                "read_only": True,
                "path": [],
            }

        visited: Set[str] = set()
        queue = deque([(source, [])])

        while queue:
            current, path = queue.popleft()

            if current in visited:
                continue

            visited.add(current)

            if current == target:
                return {
                    "status": "ok",
                    "read_only": True,
                    "path": path,
                    "length": len(path),
                }

            if len(path) >= max_depth:
                continue

            edge_ids = self.out_edges.get(current, []) + self.in_edges.get(current, [])

            for edge_id in edge_ids:
                edge = self.edges[edge_id]
                other = edge.target if edge.source == current else edge.source

                if other not in visited:
                    queue.append((other, path + [edge.to_dict()]))

        return {
            "status": "no_path",
            "read_only": True,
            "path": [],
        }

    def graph_summary(self) -> Dict[str, Any]:
        node_counts = defaultdict(int)
        edge_counts = defaultdict(int)

        for node in self.nodes.values():
            node_counts[node.node_type] += 1

        for edge in self.edges.values():
            edge_counts[edge.relation] += 1

        return {
            "status": "ok",
            "read_only": True,
            "node_counts": dict(sorted(node_counts.items())),
            "edge_counts": dict(sorted(edge_counts.items())),
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
        }

    def _ingest_memory_record(self, record: Dict[str, Any]) -> None:
        payload = record.get("payload", {}) or {}

        memory_id = record.get("memory_id")
        ticker = record.get("market_ticker")

        memory_node = self._add_node(
            node_id=f"memory:{memory_id}",
            node_type="memory",
            label=record.get("title", memory_id),
            properties={
                "memory_id": memory_id,
                "memory_type": record.get("memory_type"),
                "confidence": record.get("confidence"),
                "importance": record.get("importance"),
                "summary": record.get("summary"),
                "source_module": record.get("source_module"),
            },
        )

        if ticker:
            market_node = self._add_node(
                node_id=f"market:{ticker}",
                node_type="market",
                label=ticker,
                properties={"ticker": ticker},
            )
            self._add_edge(market_node.node_id, memory_node.node_id, "HAS_MEMORY", record.get("importance", 50) / 100.0)

        category = payload.get("category") or payload.get("event_category")
        regime = payload.get("regime")
        pattern = payload.get("pattern_name") or payload.get("name")
        strategy = payload.get("strategy")
        forecast = payload.get("forecast", {}) if isinstance(payload.get("forecast"), dict) else {}
        outcome = payload.get("outcome", {}) if isinstance(payload.get("outcome"), dict) else {}

        if category:
            node = self._add_node(f"category:{category}", "category", str(category), {})
            self._add_edge(memory_node.node_id, node.node_id, "IN_CATEGORY", 0.7)

        if regime:
            node = self._add_node(f"regime:{regime}", "regime", str(regime), {})
            self._add_edge(memory_node.node_id, node.node_id, "IN_REGIME", 0.8)

        if pattern:
            node = self._add_node(f"pattern:{pattern}", "pattern", str(pattern), {})
            self._add_edge(memory_node.node_id, node.node_id, "HAS_PATTERN", 0.85)

        if strategy:
            node = self._add_node(f"strategy:{strategy}", "strategy", str(strategy), {})
            self._add_edge(memory_node.node_id, node.node_id, "USES_STRATEGY", 0.75)

        predicted = forecast.get("predicted_side") or forecast.get("expected_resolution")
        if predicted:
            node = self._add_node(f"forecast:{predicted}", "forecast", str(predicted), {})
            self._add_edge(memory_node.node_id, node.node_id, "FORECASTED", 0.7)

        result = (
            outcome.get("result")
            or outcome.get("resolved_side")
            or outcome.get("winner")
            or payload.get("result")
            or payload.get("resolved_side")
        )

        if result:
            node = self._add_node(f"outcome:{str(result).upper()}", "outcome", str(result).upper(), {})
            self._add_edge(memory_node.node_id, node.node_id, "RESOLVED_AS", 0.9)

        for tag in record.get("tags", []) or []:
            node = self._add_node(f"tag:{tag}", "tag", str(tag), {})
            self._add_edge(memory_node.node_id, node.node_id, "TAGGED", 0.5)

    def _add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeNode:
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.properties.update(properties or {})
            return node

        node = KnowledgeNode(
            node_id=node_id,
            node_type=node_type,
            label=str(label),
            properties=properties or {},
        )
        self.nodes[node_id] = node
        return node

    def _add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeEdge:
        edge_id = f"{source}|{relation}|{target}"

        if edge_id in self.edges:
            edge = self.edges[edge_id]
            edge.weight = max(edge.weight, float(weight))
            edge.properties.update(properties or {})
            return edge

        edge = KnowledgeEdge(
            edge_id=edge_id,
            source=source,
            target=target,
            relation=relation,
            weight=float(weight),
            properties=properties or {},
        )

        self.edges[edge_id] = edge
        self.out_edges[source].append(edge_id)
        self.in_edges[target].append(edge_id)

        return edge


oracle_knowledge_graph = OracleKnowledgeGraph()
'''

test_code = r'''from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge
from qseries_v2.oracle_intelligence.oracle_knowledge_graph import OracleKnowledgeGraph


def test_oi_050_oracle_knowledge_graph():
    test_db = Path("qseries_v2") / "data" / "test_oracle_knowledge_graph.sqlite3"

    if test_db.exists():
        test_db.unlink()

    memory_engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(memory_engine, store)
    graph = OracleKnowledgeGraph(bridge)

    bridge.remember_and_persist(
        memory_type="forecast",
        market_ticker="KG-TEST-1",
        title="Knowledge graph test forecast",
        summary="A forecast memory for graph testing.",
        confidence=88,
        importance=84,
        tags=["momentum", "calibration"],
        source_module="test_oi_050",
        payload={
            "category": "crypto",
            "regime": "trend",
            "strategy": "momentum",
            "pattern_name": "strong_momentum",
            "forecast": {
                "predicted_side": "YES",
                "confidence": 88,
            },
            "outcome": {
                "result": "YES",
            },
        },
    )

    result = graph.build_from_memory()
    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["records_ingested"] == 1
    assert result["nodes"] >= 8
    assert result["edges"] >= 7

    market_nodes = graph.find_nodes(node_type="market", text="KG-TEST-1")
    assert len(market_nodes) == 1

    neighbors = graph.neighbors("market:KG-TEST-1")
    assert len(neighbors["neighbors"]) >= 1

    pattern_nodes = graph.find_nodes(node_type="pattern", text="strong_momentum")
    assert len(pattern_nodes) == 1

    path = graph.path_between("market:KG-TEST-1", "pattern:strong_momentum", max_depth=4)
    assert path["status"] == "ok"
    assert path["length"] >= 1

    summary = graph.graph_summary()
    assert summary["total_nodes"] >= 8
    assert summary["total_edges"] >= 7

    status = graph.status()
    assert status["status"] == "ok"

    print("[PASS] OI-050 Oracle Knowledge Graph")
    print({
        "build": result,
        "summary": summary,
        "path_length": path["length"],
    })


if __name__ == "__main__":
    test_oi_050_oracle_knowledge_graph()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .oracle_knowledge_graph import oracle_knowledge_graph, OracleKnowledgeGraph, KnowledgeNode, KnowledgeEdge\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-050 INSTALLER")
print(" Oracle Knowledge Graph")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-050 installed")
print()
print("Run:")
print("python test_oi_050_oracle_knowledge_graph.py")