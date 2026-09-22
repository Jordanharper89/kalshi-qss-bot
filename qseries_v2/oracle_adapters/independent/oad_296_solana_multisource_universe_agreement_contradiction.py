from __future__ import annotations
from dataclasses import dataclass
from .oad_292_solana_bounded_multisource_token_universe import discover_bounded_multisource_solana_universe
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaUniverseSourceAgreement:
 token_address:str; sources:tuple; state:str
@dataclass(frozen=True,slots=True)
class SolanaUniverseAgreementReport:
 unique_tokens:int; multi_source_tokens:int; single_source_tokens:int; rows:tuple; execution_authority:bool=False
def compare_solana_universe_source_presence(timeout_seconds=30.0):
 u=discover_bounded_multisource_solana_universe(timeout_seconds)
 rows=[]
 for c in u.candidates:
  state="MULTI_SOURCE_PRESENCE" if len(c.sources)>1 else "SINGLE_SOURCE_PRESENCE"
  rows.append(SolanaUniverseSourceAgreement(c.token_address,c.sources,state))
 multi=sum(x.state=="MULTI_SOURCE_PRESENCE" for x in rows)
 return SolanaUniverseAgreementReport(len(rows),multi,len(rows)-multi,tuple(rows),False)
