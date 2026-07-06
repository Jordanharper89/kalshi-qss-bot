import importlib

modules = {
    "OI-192": "qseries_v2.oracle_intelligence.universal_market_adapter_replay_search_engine",
    "OI-193": "qseries_v2.oracle_intelligence.universal_market_adapter_replay_filter_engine",
    "OI-194": "qseries_v2.oracle_intelligence.universal_market_adapter_replay_query_engine",
    "OI-195": "qseries_v2.oracle_intelligence.universal_market_adapter_replay_analytics_engine",
    "OI-196": "qseries_v2.oracle_intelligence.universal_market_adapter_replay_intelligence_engine",
}

for label, module_name in modules.items():
    print("\n========================================")
    print(label, module_name)
    print("========================================")
    m = importlib.import_module(module_name)

    print("Factory functions:")
    for name in dir(m):
        if name.startswith("create_"):
            print(" -", name)

    print("\nClasses and public methods:")
    for name in dir(m):
        obj = getattr(m, name)
        if isinstance(obj, type) and name.startswith("Universal"):
            print("\n", name)
            for method in dir(obj):
                if not method.startswith("_"):
                    attr = getattr(obj, method)
                    if callable(attr):
                        print("  -", method)