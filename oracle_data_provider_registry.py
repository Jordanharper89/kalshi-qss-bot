
"""
Compatibility wrapper for ORACLE-039 provider registry.
"""

from oracle_data_providers.provider_registry import (
    oracle_data_provider_registry,
    OracleProviderRegistry,
    diagnostics,
)

if __name__ == "__main__":
    print(oracle_data_provider_registry.diagnostics_text())
