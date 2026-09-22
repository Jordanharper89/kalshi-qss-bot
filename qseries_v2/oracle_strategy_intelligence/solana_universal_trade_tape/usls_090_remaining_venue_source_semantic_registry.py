from __future__ import annotations
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
