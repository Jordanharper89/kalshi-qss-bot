\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .oad_339_solana_reconciled_program_identity_registry import identify_reconciled_program
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaUnknownProgramTriage:
 total_unknown:int;unique_unknown:int;top_unknown:tuple;execution_authority:bool=False
def triage_unknown_programs(attributions):
 c=Counter()
 for a in attributions:
  for pid in tuple(a.top_level_program_ids)+tuple(a.inner_program_ids):
   x=identify_reconciled_program(pid)
   if not x.known:c[pid]+=1
 return SolanaUnknownProgramTriage(sum(c.values()),len(c),tuple(c.most_common(50)),False)

