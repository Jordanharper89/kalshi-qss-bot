import importlib
import py_compile
from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

print("========================================")
print(" ORACLE REPLAY SMOKE GATE V1")
print(" OI-192 → OI-196 Canonical ReplayResult Integration Gate")
print("========================================")

print("\n[1] Compiling Oracle Intelligence modules...")
compiled = 0
for path in sorted(PKG.glob("*.py")):
    py_compile.compile(str(path), doraise=True)
    compiled += 1
print(f"[OK] Compiled {compiled} Oracle files")

print("\n[2] Importing OI-192 through OI-196...")
m192 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_search_engine")
m193 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_filter_engine")
m194 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_query_engine")
m195 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_analytics_engine")
m196 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_intelligence_engine")
print("[OK] Imported replay modules")

records = [
        {"registration_id": "reg-001", "certification_id": "cert-001", "manifest_id": "manifest-001", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTA", "status": "registered", "certification_level": "certified", "certified": True, "confidence": 0.91},
        {"registration_id": "reg-002", "certification_id": "cert-002", "manifest_id": "manifest-002", "adapter_id": "adp.kalshi", "market_type": "prediction_market", "symbol": "TESTB", "status": "registered", "certification_level": "certified_with_warnings", "certified": True, "confidence": 0.74},
        {"registration_id": "reg-003", "certification_id": "cert-003", "manifest_id": "manifest-003", "adapter_id": "adp.polymarket", "market_type": "prediction_market", "symbol": "TESTC", "status": "rejected", "certification_level": "not_certified", "certified": False, "confidence": 0.42},
    ]

print("\n[3] OI-192 Search...")
search_engine = m192.create_replay_search_engine("oracle.replay_smoke_gate.v1")
search_engine.load_registry_records(records)
search = search_engine.search_by_adapter("adp.kalshi")
assert search.passed is True
assert search.record_count == 2
print("[OK] Search returned ReplayResult with 2 records")

print("\n[4] OI-193 Filter...")
filter_engine = m193.create_replay_filter_engine("oracle.replay_smoke_gate.v1")
filtered = filter_engine.filter_records(search, {"certified": True, "min_confidence": 0.70})
assert filtered.passed is True
assert filtered.record_count == 2
print("[OK] Filter returned ReplayResult with 2 records")

print("\n[5] OI-194 Query...")
query_engine = m194.create_replay_query_engine("oracle.replay_smoke_gate.v1")
query = query_engine.query(filtered, {"select": ["registration_id", "manifest_id", "certification_level", "confidence", "certified"], "sort_by": "confidence", "sort_order": "desc"})
assert query.passed is True
assert query.record_count == 2
assert query.records[0]["confidence"] >= query.records[1]["confidence"]
print("[OK] Query returned ReplayResult sorted by confidence")

print("\n[6] OI-195 Analytics...")
analytics_engine = m195.create_replay_analytics_engine("oracle.replay_smoke_gate.v1")
analytics = analytics_engine.analyze(query)
assert analytics.passed is True
assert analytics.metadata["record_count"] == 2
assert analytics.metadata["certified_count"] == 2
print("[OK] Analytics returned ReplayResult summary")

print("\n[7] OI-196 Intelligence...")
intelligence_engine = m196.create_replay_intelligence_engine("oracle.replay_smoke_gate.v1")
intelligence = intelligence_engine.generate_intelligence(query, analytics=analytics, context={"gate": "replay_smoke_gate_v1"})
assert intelligence.passed is True
assert intelligence.metadata["record_count"] == 2
assert intelligence.metadata["certified_count"] == 2
print("[OK] Intelligence returned ReplayResult insight")

print("\n[8] Canonical contract and read-only guardrail check...")
for label, result in {"OI-192": search, "OI-193": filtered, "OI-194": query, "OI-195": analytics, "OI-196": intelligence}.items():
    assert hasattr(result, "records")
    assert hasattr(result, "passed")
    assert hasattr(result, "record_count")
    assert hasattr(result, "telemetry")
    assert hasattr(result, "explainability")
    assert result.read_only_guardrails["oracle_read_only"] is True
    assert result.read_only_guardrails["executes_trades"] is False
    assert result.read_only_guardrails["routes_orders"] is False
    assert result.read_only_guardrails["submits_orders"] is False
    assert result.read_only_guardrails["manages_positions"] is False
    assert result.read_only_guardrails["execution_owner"] == "Q_SERIES_ONLY"
    print(f"[OK] {label} ReplayResult contract and guardrails intact")

print("\n========================================")
print("[PASS] ORACLE REPLAY SMOKE GATE V1")
print("OI-192 → OI-196 integration passed using canonical ReplayResult.")
print("No execution authority was created.")
print("Q Series remains the only execution engine.")
print("========================================")
