from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OLC-008"
OLC_008_REVISION = "OLC_008_COMMAND_REGISTRY_CONTRACT_RESOLVER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class CommandRegistryContract:
    module_name: str
    builder_name: str
    registry_type: str
    registry_kind: str
    ask_command_present: bool
    ask_resolution_mode: str
    ask_resolution_path: str
    ask_entry_type: str | None
    ask_entry_callable: bool
    read_only: bool


def verify_command_registry_contract_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_008_REVISION",
    "CommandRegistryContract",
    "verify_command_registry_contract_resolver",
]
