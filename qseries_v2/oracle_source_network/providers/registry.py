from dataclasses import dataclass
from typing import Dict, Iterable

@dataclass(frozen=True)
class ProviderSpec:
    provider_id: str
    sports: tuple
    authority: str
    base_url: str
    read_only: bool = True
    execution_authority: bool = False

_REGISTRY: Dict[str, ProviderSpec] = {}

def register(spec: ProviderSpec) -> None:
    if not spec.read_only or spec.execution_authority:
        raise ValueError("OSN providers must be read-only and non-executing")
    if spec.provider_id in _REGISTRY and _REGISTRY[spec.provider_id] != spec:
        raise ValueError("provider id collision")
    _REGISTRY[spec.provider_id] = spec

def get(provider_id: str) -> ProviderSpec:
    return _REGISTRY[provider_id]

def all_providers() -> Iterable[ProviderSpec]:
    return tuple(_REGISTRY.values())
