from __future__ import annotations
from dataclasses import dataclass,asdict
import json
from pathlib import Path

@dataclass(frozen=True)
class SolanaPoolBirthEvent:
 token_address:str
 pair_address:str
 launcher_family:str
 dex_id:str|None
 pair_created_at_ms:int|None
 oracle_observed_at:str
 price_usd:float|None
 market_cap:float|None
 fdv:float|None
 liquidity_usd:float|None
 volume_h24:float|None
 buys_h24:int|None
 sells_h24:int|None
 source_id:str
 source_provider:str|None
 source_observation_type:str|None
 execution_authority:bool=False

def verify(x):
 return (
  bool(x.token_address) and bool(x.pair_address) and bool(x.oracle_observed_at)
  and bool(x.source_id) and x.execution_authority is False
 )

def write_fixture(root):
 x=SolanaPoolBirthEvent("TOKEN","PAIR","OTHER",None,None,"2026-01-01T00:00:00+00:00",
  None,None,None,None,None,None,None,"source.fixture",None,None,False)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/pool_birth_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(asdict(x),indent=2,sort_keys=True),encoding="utf-8")
 return p,x
