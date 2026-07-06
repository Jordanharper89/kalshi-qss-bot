import importlib
from pprint import pprint

m193 = importlib.import_module("qseries_v2.oracle_intelligence.universal_market_adapter_replay_filter_engine")

records = [
    {"registration_id": "reg-001", "certified": True, "confidence": 0.91},
    {"registration_id": "reg-002", "certified": True, "confidence": 0.74},
]

engine = m193.create_replay_filter_engine("inspect.oi193")

tests = [
    {"certified": True, "min_confidence": 0.70},
    {"certified": True},
    {"min_confidence": 0.70},
    {"confidence_min": 0.70},
    {"minimum_confidence": 0.70},
    {"field": "certified", "equals": True},
]

for criteria in tests:
    print("\nCRITERIA:", criteria)
    try:
        result = engine.filter_records(records, criteria)
        pprint(result.to_dict() if hasattr(result, "to_dict") else result)
    except Exception as e:
        print("ERROR:", type(e).__name__, e)

