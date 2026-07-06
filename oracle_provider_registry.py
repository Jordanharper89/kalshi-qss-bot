
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
