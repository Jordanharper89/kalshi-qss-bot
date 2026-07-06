from pathlib import Path

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
