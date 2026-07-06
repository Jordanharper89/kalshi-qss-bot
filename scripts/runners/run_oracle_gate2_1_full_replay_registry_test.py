import importlib
import py_compile
from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

def is_good(obj):
    if hasattr(obj, "passed"):
        return obj.passed is True
    if hasattr(obj, "certified"):
        return obj.certified is True
    if hasattr(obj, "status"):
        return str(obj.status).lower() in {"pass", "passed", "certified", "ok", "valid", "registered"}
    if hasattr(obj, "to_dict"):
        d = obj.to_dict()
    elif hasattr(obj, "__dict__"):
        d = obj.__dict__
    else:
        d = {}
    return (
        d.get("passed") is True
        or d.get("certified") is True
        or str(d.get("status", "")).lower() in {"pass", "passed", "certified", "ok", "valid", "registered"}
    )

print("========================================")
print(" ORACLE GATE 2.1 FULL REPLAY REGISTRY TEST")
print(" Audit → Index → Manifest → Validation → Certification → Registry → Lookup")
print("========================================")

print("\n[1] Compiling Oracle Intelligence modules...")
compiled = 0
for path in sorted(PKG.glob("*.py")):
    py_compile.compile(str(path), doraise=True)
    compiled += 1
print(f"[OK] Compiled {compiled} Oracle files")

print("\n[2] Importing OI-185 through OI-191...")
m185 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_engine")
m186 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_index_engine")
m187 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_manifest_engine")
m188 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_validation_engine")
m189 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_certification_engine")
m190 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_engine")
m191 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_lookup_engine")
print("[OK] Imported replay registry pipeline")

print("\n[3] Creating fake read-only query audit...")
audit_engine = m185.create_query_audit_engine("oracle.gate2.1")
audit_record = audit_engine.audit_query(
    adapter_id="adp.gate2.fake",
    query={"query_id": "gate2-1-query-001", "market_type": "prediction_market", "market": "FAKE_GATE_2_1_MARKET"},
    resolver_output={"query_id": "gate2-1-query-001", "resolved": True, "markets": [{"universal_market_id": "umm.gate2.1.fake.001"}]},
    market_model={"schema_version": "1.0", "universal_market_id": "umm.gate2.1.fake.001", "market_type": "prediction_market"},
    telemetry={"source": "oracle_gate2_1_full_replay_registry_test"},
)
assert audit_record.passed is True
print("[OK] OI-185 audit passed")

print("\n[4] Indexing audit record...")
index_engine = m186.create_query_audit_index_engine("oracle.gate2.1")
index_summary = index_engine.index_records([audit_record])
assert index_summary.entry_count == 1
print("[OK] OI-186 index passed")

print("\n[5] Building replay manifest...")
manifest_engine = m187.create_query_replay_manifest_engine("oracle.gate2.1")
manifest = manifest_engine.build_from_index_engine(
    index_engine,
    manifest_context={"test_name": "oracle_gate2_1_full_replay_registry_test"},
)
assert manifest.entry_count == 1
print("[OK] OI-187 replay manifest passed")

print("\n[6] Validating replay manifest...")
validation_engine = m188.create_query_replay_validation_engine("oracle.gate2.1")
validation = validation_engine.validate_manifest(manifest)
assert validation.passed is True
print("[OK] OI-188 replay validation passed")

print("\n[7] Certifying replay validation...")
cert_engine = m189.create_query_replay_certification_engine("oracle.gate2.1")
certification = cert_engine.certify_validation(
    validation,
    manifest=manifest,
    certification_context={"gate": "2.1", "scope": "full_replay_registry_test"},
)
assert is_good(certification), "Certification did not certify"
print("[OK] OI-189 replay certification passed")

print("\n[8] Registering certified replay artifact...")
registry_engine = m190.create_replay_registry_engine("oracle.gate2.1")
registration = registry_engine.register_certification(
    certification,
    manifest=manifest,
    validation=validation,
)
assert is_good(registration), "Registry registration failed"
print("[OK] OI-190 replay registry registration passed")

print("\n[9] Looking up registry artifact...")
lookup_engine = m191.create_replay_registry_lookup_engine("oracle.gate2.1")
lookup_engine.load_registry_records(registry_engine.records())

registration_id = getattr(registration, "registration_id", registration.to_dict().get("registration_id"))
certification_id = getattr(certification, "certification_id", certification.to_dict().get("certification_id"))

assert lookup_engine.lookup_by_registration_id(registration_id) is not None
assert len(lookup_engine.lookup_by_manifest_id(manifest.manifest_id)) >= 1
assert len(lookup_engine.lookup_by_certification_id(certification_id)) >= 1
print("[OK] OI-191 replay registry lookup passed")

print("\n[10] Read-only guardrail check...")
for name, module in {
    "OI-185": m185,
    "OI-186": m186,
    "OI-187": m187,
    "OI-188": m188,
    "OI-189": m189,
    "OI-190": m190,
    "OI-191": m191,
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
print("[PASS] ORACLE GATE 2.1 FULL REPLAY REGISTRY TEST")
print("Oracle completed full replay registry chain successfully.")
print("No execution authority was created.")
print("Q Series remains the only execution engine.")
print("========================================")