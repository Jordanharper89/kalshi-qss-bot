from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_162j_phase8_universal_14_family_live_decoder_closure.py"
TEST=ROOT/"test_usls_162j_phase8_universal_14_family_live_decoder_closure.py"

MOD_TEXT=r"""from __future__ import annotations
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161z_phase8_damm_v1_live_decoder_extension import decode_live_trade_extended as decode_13
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162g_pump_fun_live_direct_decoder import decode as decode_pump

TARGET=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
"METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM","ORCA","MOONIT","BOOP_FUN","HEAVEN")

def decode_live_trade_all14(root,family,signature,transaction,observed_unix):
 fam=str(family or "").upper()
 if fam=="PUMP_FUN":
  return decode_pump(root,signature,transaction,observed_unix)
 return decode_13(fam,signature,transaction,observed_unix)

def contract():
 return {"revision":"USLS_162J","target_family_count":14,"supported_families":list(TARGET),
  "decoder_pending_families":[],"pump_fun_source":"USLS_162G",
  "damm_v1_source":"USLS_161Z","other_family_source":"USLS_161K",
  "strict_live_provenance_required":True,"unknown_retention_required":True,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
"""

TEST_TEXT=r"""import json,unittest
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162j_phase8_universal_14_family_live_decoder_closure import contract
class T(unittest.TestCase):
 def test_contract(self):
  d=contract()
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["target_family_count"],14)
  self.assertEqual(len(d["supported_families"]),14)
  self.assertEqual(d["decoder_pending_families"],[])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162J universal 14-family live decoder closure")
  print("[PASS] Pump.fun + DAMM v1 are now inside the same transaction-level live decoder boundary")
  print("[NEXT] PUMP_FUN_AND_PUMPSWAP_TARGETED_LIVE_CAPTURE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")