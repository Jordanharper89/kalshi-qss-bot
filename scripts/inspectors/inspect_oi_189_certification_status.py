import importlib
from pprint import pprint

m185 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_engine")
m186 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_index_engine")
m187 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_manifest_engine")
m188 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_validation_engine")
m189 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_certification_engine")

audit = m185.create_query_audit_engine("oracle.inspect").audit_query(
    adapter_id="adp.inspect.fake",
    query={"query_id": "inspect-q-001", "market_type": "prediction_market", "market": "FAKE"},
    resolver_output={"query_id": "inspect-q-001", "resolved": True, "markets": [{"universal_market_id": "umm.inspect.001"}]},
    market_model={"schema_version": "1.0", "universal_market_id": "umm.inspect.001", "market_type": "prediction_market"},
)

idx = m186.create_query_audit_index_engine("oracle.inspect")
idx.index_records([audit])

manifest = m187.create_query_replay_manifest_engine("oracle.inspect").build_from_index_engine(idx)
validation = m188.create_query_replay_validation_engine("oracle.inspect").validate_manifest(manifest)
cert = m189.create_query_replay_certification_engine("oracle.inspect").certify_validation(validation)

print("\nVALIDATION:")
pprint(validation.to_dict())

print("\nCERTIFICATION:")
pprint(cert.to_dict())