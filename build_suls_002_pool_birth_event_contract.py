from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_002_pool_birth_event_contract.py"
TEST=ROOT/"test_suls_002_pool_birth_event_contract.py"

MOD_TEXT=r"""from __future__ import annotations
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
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_002_pool_birth_event_contract import write_fixture,verify
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,x=write_fixture(ROOT);self.assertTrue(verify(x));self.assertFalse(x.execution_authority)
  print("[PASS] SULS-002 canonical pool-birth event contract")
  print("[SCOPE] Contract certification only; fixture does not claim live observation")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-002 CANONICAL POOL-BIRTH EVENT CONTRACT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
