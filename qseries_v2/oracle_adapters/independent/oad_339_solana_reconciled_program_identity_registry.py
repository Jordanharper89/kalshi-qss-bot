\

from __future__ import annotations
from dataclasses import dataclass
from .oad_333_solana_authoritative_program_identity_registry import identify_solana_program
from .oad_338_solana_token2022_memo_foundation_repair import identify_foundation_program
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaReconciledProgramIdentity:
 program_id:str;name:str;category:str;known:bool;market_relevant:bool;source:str;execution_authority:bool=False
def identify_reconciled_program(program_id):
 f=identify_foundation_program(program_id)
 if f.name!="UNRESOLVED":return SolanaReconciledProgramIdentity(f.program_id,f.name,f.category,True,f.market_relevant,"FOUNDATION_REPAIR",False)
 x=identify_solana_program(program_id)
 return SolanaReconciledProgramIdentity(x.program_id,x.name,x.category,x.known,x.market_relevant,"OAD_333" if x.known else "UNRESOLVED",False)

