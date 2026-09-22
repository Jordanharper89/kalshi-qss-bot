\

from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

PROGRAMS={
    "11111111111111111111111111111111":("SYSTEM","INFRASTRUCTURE"),
    "ComputeBudget111111111111111111111111111111":("COMPUTE_BUDGET","INFRASTRUCTURE"),
    "Vote111111111111111111111111111111111111111":("SOLANA_VOTE","INFRASTRUCTURE"),
    "Stake11111111111111111111111111111111111111":("SOLANA_STAKE","INFRASTRUCTURE"),
    "AddressLookupTab1e1111111111111111111111111":("ADDRESS_LOOKUP_TABLE","INFRASTRUCTURE"),
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":("SPL_TOKEN","TOKEN"),
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL":("ASSOCIATED_TOKEN","TOKEN"),
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4":("JUPITER_V6","ROUTER"),
    "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P":("PUMP_FUN_BONDING_CURVE","DEX_LAUNCH"),
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA":("PUMP_FUN_AMM","DEX"),
    "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ":("PUMP_FUN_FEES","DEX_SUPPORT"),
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo":("METEORA_DLMM","DEX"),
}

@dataclass(frozen=True,slots=True)
class SolanaProgramIdentity:
    program_id:str
    name:str
    category:str
    known:bool
    market_relevant:bool
    execution_authority:bool=False

def identify_solana_program(program_id):
    pid=str(program_id or "")
    name,cat=PROGRAMS.get(pid,("UNKNOWN_PROGRAM","UNKNOWN"))
    market=cat not in ("INFRASTRUCTURE","UNKNOWN")
    return SolanaProgramIdentity(pid,name,cat,pid in PROGRAMS,market,False)

def authoritative_program_registry():
    return tuple(identify_solana_program(x) for x in PROGRAMS)

