
"""Multi-league official-source provider catalog."""
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass(frozen=True)
class LeagueProvider:
    provider_id: str
    league: str
    authority: str
    official_domain: str
    acquisition_mode: str
    read_only: bool = True
    execution_authority: bool = False

_REGISTRY: Dict[str, LeagueProvider] = {}

def register(spec: LeagueProvider):
    if not spec.read_only or spec.execution_authority:
        raise ValueError("OSN providers must remain read-only")
    key = spec.league.upper()
    if key in _REGISTRY and _REGISTRY[key] != spec:
        raise ValueError(f"league provider collision: {key}")
    _REGISTRY[key] = spec

def get(league: str):
    return _REGISTRY[league.upper()]

def has(league: str) -> bool:
    return league.upper() in _REGISTRY

def all_specs() -> Tuple[LeagueProvider, ...]:
    return tuple(_REGISTRY[k] for k in sorted(_REGISTRY))
