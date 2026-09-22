\
from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

TOKEN_2022_PROGRAM_ID="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
MEMO_PROGRAM_ID="MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

@dataclass(frozen=True,slots=True)
class SolanaFoundationProgramIdentity:
    program_id:str
    name:str
    category:str
    market_relevant:bool
    execution_authority:bool=False

def identify_foundation_program(program_id):
    pid=str(program_id or "")
    if pid==TOKEN_2022_PROGRAM_ID:
        return SolanaFoundationProgramIdentity(pid,"TOKEN_2022","TOKEN",True,False)
    if pid==MEMO_PROGRAM_ID:
        return SolanaFoundationProgramIdentity(pid,"MEMO","INFRASTRUCTURE",False,False)
    return SolanaFoundationProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False)
