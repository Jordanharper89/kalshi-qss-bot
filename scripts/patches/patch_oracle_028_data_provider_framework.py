from pathlib import Path

root = Path.cwd()

provider_file = root / "oracle_data_provider.py"
registry_file = root / "oracle_provider_registry.py"
bot_file = root / "telegram_bot.py"

provider_file.write_text(r'''
"""
ORACLE-028 — Data Provider Framework

Purpose:
- Standard interface for all Oracle data sources.
- Future providers: Kalshi, news, weather, sports, economic calendar, sentiment.
"""

import time


class OracleDataProvider:
    name = "base"

    def fetch(self):
        return {
            "provider": self.name,
            "status": "empty",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "markets": [],
            "signals": [],
            "errors": [],
        }


class MockKalshiProvider(OracleDataProvider):
    name = "mock_kalshi"

    def fetch(self):
        return {
            "provider": self.name,
            "status": "ok",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "markets": [],
            "signals": [],
            "errors": [],
        }
''', encoding="utf-8")

registry_file.write_text(r'''
"""
ORACLE-028 — Provider Registry
"""

from oracle_data_provider import MockKalshiProvider


class OracleProviderRegistry:
    def __init__(self):
        self.providers = []

    def register(self, provider):
        self.providers.append(provider)

    def fetch_all(self):
        results = []
        for provider in self.providers:
            try:
                results.append(provider.fetch())
            except Exception as e:
                results.append({
                    "provider": getattr(provider, "name", "unknown"),
                    "status": "error",
                    "markets": [],
                    "signals": [],
                    "errors": [str(e)],
                })
        return results

    def diagnostics_text(self):
        return (
            "ORACLE DATA PROVIDERS\n\n"
            f"Providers loaded: {len(self.providers)}\n"
            + "\n".join(f"- {p.name}" for p in self.providers)
        )


oracle_provider_registry = OracleProviderRegistry()
oracle_provider_registry.register(MockKalshiProvider())
''', encoding="utf-8")

print("[OK] Created oracle_data_provider.py")
print("[OK] Created oracle_provider_registry.py")

if bot_file.exists():
    text = bot_file.read_text(encoding="utf-8")

    if "from oracle_provider_registry import oracle_provider_registry" not in text:
        text = "from oracle_provider_registry import oracle_provider_registry\n" + text
        print("[OK] Added provider registry import")

    marker = "oracle_research_engine.start()"
    if marker in text and "oracle_provider_registry.fetch_all()" not in text:
        text = text.replace(
            marker,
            marker + "\n    print(oracle_provider_registry.diagnostics_text())",
            1
        )
        print("[OK] Added provider diagnostics at startup")

    bot_file.write_text(text, encoding="utf-8")

print("[DONE] ORACLE-028 patch applied")