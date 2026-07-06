from pathlib import Path
import importlib
import py_compile
import traceback

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

print("========================================")
print(" ORACLE GATE 2 FIRST TEST RUN")
print(" Read-Only Integration Smoke Test")
print("========================================")

assert PKG.exists(), f"Missing Oracle package: {PKG}"

print("\n[1] Compiling Oracle Intelligence modules...")
compiled = 0
for path in sorted(PKG.glob("*.py")):
    py_compile.compile(str(path), doraise=True)
    compiled += 1
print(f"[OK] Compiled {compiled} Oracle files")

print("\n[2] Importing replay pipeline modules...")
m185 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_engine")
m186 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_index_engine")
m187 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_manifest_engine")
m188 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_validation_engine")
m189 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_certification_engine")
m190 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_engine")
m191 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_lookup_engine")
print("[OK] Imported OI-185 through OI-191")

print("\n[3] Running fake read-only adapter query through Oracle replay pipeline...")

audit_engine = m185.create_query_audit_engine("oracle.gate2.first_test")
audit_record = audit_engine.audit_query(
    adapter_id="adp.gate2.fake",
    query={
        "query_id": "gate2-query-001",
        "market_type": "prediction_market",
        "market": "FAKE_TEST_MARKET",
        "symbol": "ORACLE_TEST",
    },
    resolver_output={
        "query_id": "gate2-query-001",
        "resolved": True,
        "markets": [{"universal_market_id": "umm.gate2.fake.001"}],
    },
    market_model={
        "schema_version": "1.0",
        "universal_market_id": "umm.gate2.fake.001",
        "market_type": "prediction_market",
    },
    telemetry={"source": "oracle_gate2_first_test"},
)

assert audit_record.passed is True
print("[OK] OI-185 audit passed")

index_engine = m186.create_query_audit_index_engine("oracle.gate2.first_test")
index_summary = index_engine.index_records([audit_record])
assert index_summary.entry_count == 1
print("[OK] OI-186 index passed")

manifest_engine = m187.create_query_replay_manifest_engine("oracle.gate2.first_test")
manifest = manifest_engine.build_from_index_engine(
    index_engine,
    manifest_context={"test_name": "oracle_gate2_first_test"},
)
assert manifest.entry_count == 1
print("[OK] OI-187 replay manifest passed")

validation_engine = m188.create_query_replay_validation_engine("oracle.gate2.first_test")
validation = validation_engine.validate_manifest(manifest)
assert validation.passed is True
print("[OK] OI-188 replay validation passed")

print("\n[4] Verifying OI-189/OI-190/OI-191 import readiness...")
print("[OK] OI-189 certification module import-ready")
print("[OK] OI-190 registry module import-ready")
print("[OK] OI-191 registry lookup module import-ready")

print("\n[5] Oracle read-only guardrail check...")
for name, module in {
    "OI-185": m185,
    "OI-186": m186,
    "OI-187": m187,
    "OI-188": m188,
}.items():
    guardrails = getattr(module, "READ_ONLY_GUARDRAILS")
    assert guardrails["oracle_read_only"] is True
    assert guardrails["executes_trades"] is False
    assert guardrails["routes_orders"] is False
    assert guardrails["submits_orders"] is False
    assert guardrails["manages_positions"] is False
    assert guardrails["execution_owner"] == "Q_SERIES_ONLY"
    print(f"[OK] {name} read-only guardrails intact")

print("\n========================================")
print("[PASS] ORACLE GATE 2 FIRST TEST RUN")
print("Oracle compiled, imported, audited, indexed, replayed, and validated successfully.")
print("No execution authority was created.")
print("Q Series remains the only execution engine.")
print("========================================")