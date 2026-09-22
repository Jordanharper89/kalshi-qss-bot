from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_414_oracle_source_capability_inventory import inventory_source_capabilities
READ_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class SourceRegistryEntry:
 source_family:str; authority:str; existing_modules:tuple[str,...]; active:bool
TARGETS=(('NWS/NOAA','AUTHORITATIVE'),('USGS','AUTHORITATIVE'),('SPORTS_OFFICIAL','PRIMARY'),('MLB_OFFICIAL','PRIMARY'),('NHL_OFFICIAL','PRIMARY'),('BLS','AUTHORITATIVE'),('ECONOMIC_OFFICIAL','AUTHORITATIVE'),('CDC','AUTHORITATIVE'),('PUBLIC_HEALTH_OFFICIAL','AUTHORITATIVE'),('COINBASE','PRIMARY'),('BITCOIN_CHAIN','PRIMARY'),('ETHEREUM_CHAIN','PRIMARY'),('SOLANA_CHAIN','PRIMARY'),('FEDERAL_REGISTER','AUTHORITATIVE'),('REDDIT','SOCIAL_SIGNAL'),('X/TWITTER','SOCIAL_SIGNAL'),('NEWS','SECONDARY_HIGH_RELIABILITY'),('EIA','AUTHORITATIVE'),('SEC_EDGAR','AUTHORITATIVE'),('ELECTION_OFFICIAL','AUTHORITATIVE'),('NASA','AUTHORITATIVE'),('FAA','AUTHORITATIVE'))
def build_source_registry(root='.'):
 caps=inventory_source_capabilities(root); out=[]
 for fam,auth in TARGETS:
  mods=tuple(sorted(x.module for x in caps if x.source_family==fam))
  out.append(SourceRegistryEntry(fam,auth,mods,bool(mods)))
 return tuple(out)
def registry_by_family(root='.'):
 return {x.source_family:x for x in build_source_registry(root)}
