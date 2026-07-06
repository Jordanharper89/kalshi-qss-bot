from pathlib import Path

ROOT = Path.cwd()
INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

text = INIT.read_text(encoding="utf-8")

text = text.replace(
    "from .universal_market_adapter_replay_filter_engine import UniversalMarketAdapterReplayFilterEngine, ReplayFilterCriteria, create_replay_filter_engine",
    "from .universal_market_adapter_replay_filter_engine import UniversalMarketAdapterReplayFilterEngine, create_replay_filter_engine",
)

INIT.write_text(text, encoding="utf-8")

print("========================================")
print(" REPLAY CONTRACT REFACTOR INIT FIX")
print("========================================")
print(f"[OK] Patched {INIT}")
print()
print("Run:")
print("py test_oi_192_universal_market_adapter_replay_search_engine.py")
print("py test_oi_193_universal_market_adapter_replay_filter_engine.py")
print("py test_oi_194_universal_market_adapter_replay_query_engine.py")
print("py test_oi_195_universal_market_adapter_replay_analytics_engine.py")
print("py test_oi_196_universal_market_adapter_replay_intelligence_engine.py")
print("py run_oracle_replay_smoke_gate_v1.py")