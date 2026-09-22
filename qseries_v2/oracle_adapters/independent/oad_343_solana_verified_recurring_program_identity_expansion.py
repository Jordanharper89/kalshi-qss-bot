\

from __future__ import annotations
from dataclasses import dataclass
from .oad_339_solana_reconciled_program_identity_registry import identify_reconciled_program

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

PHOENIX_ETERNAL_PROGRAM_ID="EtrnLzgbS7nMMy5fbD42kXiUzGg8XQzJ972Xtk1cjWih"
ARCHER_EXCHANGE_PROGRAM_ID="Archer8kgiavM61GyusMzaaS2ft5sALtNsD1HxkUPMhy"
PYTH_PRICE_FEED_PROGRAM_ID="pythWSnswVUd12oZpeFP8e9CVaEqJg25g1Vtc2biRsT"

@dataclass(frozen=True,slots=True)
class SolanaExpandedProgramIdentity:
    program_id:str
    name:str
    category:str
    known:bool
    market_relevant:bool
    evidence_class:str
    execution_authority:bool=False

_EXPANSION={
    PHOENIX_ETERNAL_PROGRAM_ID:("PHOENIX_ETERNAL","ORDER_BOOK_DEX",True,"PUBLISHED_PROGRAM_CONSTANT"),
    ARCHER_EXCHANGE_PROGRAM_ID:("ARCHER_EXCHANGE","ORDER_BOOK_DEX",True,"PUBLIC_PROGRAM_LABEL_PLUS_DEX_INDEX"),
    PYTH_PRICE_FEED_PROGRAM_ID:("PYTH_PRICE_FEED","ORACLE_INFRASTRUCTURE",False,"OFFICIAL_PYTH_CONTRACT_ADDRESS"),
}

def identify_expanded_program(program_id):
    pid=str(program_id or "")
    base=identify_reconciled_program(pid)
    if base.known:
        return SolanaExpandedProgramIdentity(
            pid,base.name,base.category,True,base.market_relevant,
            "OAD_339_RECONCILED",False
        )
    x=_EXPANSION.get(pid)
    if x:
        return SolanaExpandedProgramIdentity(pid,x[0],x[1],True,x[2],x[3],False)
    return SolanaExpandedProgramIdentity(pid,"UNRESOLVED","UNKNOWN",False,False,"UNRESOLVED",False)

