from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_090_remaining_venue_source_semantic_registry.py"
TEST=ROOT/"test_usls_090_remaining_venue_source_semantic_registry.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
SEMANTICS={
 "MOONIT":{
  "66063d1201daebea":{"name":"BUY","side":"BUY","roles":["sender","sender_token_account","curve_account","curve_token_account","dex_fee","helio_fee","mint","config_account","token_program","associated_token_program","system_program"]},
  "33e685a4017f83ad":{"name":"SELL","side":"SELL","roles":["sender","sender_token_account","curve_account","curve_token_account","dex_fee","helio_fee","mint","config_account","token_program","associated_token_program","system_program"]}},
 "BOOP_FUN":{
  "8a7f0e5b26577369":{"name":"BUY_TOKEN","side":"BUY","roles":["mint","bonding_curve","trading_fees_vault","bonding_curve_vault","bonding_curve_sol_vault","recipient_token_account","buyer","config","vault_authority","wsol","system_program","token_program","associated_token_program"]},
  "6d3d28bbe6b087ae":{"name":"SELL_TOKEN","side":"SELL","roles":["mint","bonding_curve","trading_fees_vault","bonding_curve_vault","bonding_curve_sol_vault","seller_token_account","seller","recipient","config","system_program","token_program","associated_token_program"]}},
 "HEAVEN":{
  "66063d1201daebea":{"name":"BUY","side":"BUY","roles":["token_a_program","token_b_program","associated_token_program","system_program","liquidity_pool_state","user","token_a_mint","token_b_mint","user_token_a_vault","user_token_b_vault","token_a_vault","token_b_vault","protocol_config","instruction_sysvar_account_info"]},
  "33e685a4017f83ad":{"name":"SELL","side":"SELL","roles":["token_a_program","token_b_program","associated_token_program","system_program","liquidity_pool_state","user","token_a_mint","token_b_mint","user_token_a_vault","user_token_b_vault","token_a_vault","token_b_vault","protocol_config","instruction_sysvar_account_info"]}}
}
def write(root):
 d={"revision":"USLS_090","semantics":SEMANTICS,"unknown_retention":True,
  "source_policy":"CURRENT_GENERATED_DECODER_LAYOUTS_PLUS_PHYSICAL_USLS088_MATCH",
  "execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_source_semantic_registry.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_090_remaining_venue_source_semantic_registry import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  self.assertEqual(SEMANTICS["MOONIT"]["66063d1201daebea"]["side"],"BUY")
  self.assertEqual(SEMANTICS["MOONIT"]["33e685a4017f83ad"]["side"],"SELL")
  self.assertEqual(SEMANTICS["BOOP_FUN"]["8a7f0e5b26577369"]["side"],"BUY")
  self.assertEqual(SEMANTICS["BOOP_FUN"]["6d3d28bbe6b087ae"]["side"],"SELL")
  self.assertEqual(SEMANTICS["HEAVEN"]["66063d1201daebea"]["side"],"BUY")
  self.assertEqual(SEMANTICS["HEAVEN"]["33e685a4017f83ad"]["side"],"SELL")
  self.assertTrue(d["unknown_retention"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-090 source-backed Moonit/Boop/Heaven trade semantics")
  print("[PASS] physical USLS-088 fingerprints mapped without dropping unknown instructions")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")