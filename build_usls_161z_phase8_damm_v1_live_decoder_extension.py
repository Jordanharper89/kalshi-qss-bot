from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161z_phase8_damm_v1_live_decoder_extension.py"
TEST=ROOT/"test_usls_161z_phase8_damm_v1_live_decoder_extension.py"
MOD_TEXT=r"""from __future__ import annotations
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161k_phase8_universal_live_economics_producer_rebuild import decode_live_trade,SUPPORTED as BASE_SUPPORTED
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_075_meteora_damm_v1_program_correction import CORRECT_PROGRAM,SWAP_DISC
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_077_meteora_damm_v1_exact_swap_decoder import b58d,keys,all_ix
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_082b_meteora_damm_v1_exact_vault_direction_repair import token_meta,transfers,total,parent

SUPPORTED=tuple(list(BASE_SUPPORTED)+["METEORA_DAMM_V1"])

def decode_damm_v1(signature,tx,observed_unix):
 ks=keys(tx);out=[]
 for level,ordinal,ix in all_ix(tx):
  pid=ix.get("programId")
  if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
  if pid!=CORRECT_PROGRAM or not ix.get("data") or b58d(ix["data"])[:8]!=SWAP_DISC:continue
  ac=ix.get("accounts") or [];ac=[ks[a] if isinstance(a,int) and a<len(ks) else a for a in ac]
  if len(ac)<=12:continue
  pool,us,ud,av,bv,trader=ac[0],ac[1],ac[2],ac[5],ac[6],ac[12]
  tm=token_meta(tx);ts=transfers(tx,parent(level,ordinal),tm)
  ai=total(ts,us,av);bi=total(ts,us,bv);ao=total(ts,av,ud);bo=total(ts,bv,ud)
  econ=None
  if ai is not None and bo is not None:
   am=tm.get(av,{}).get("mint");bm=tm.get(bv,{}).get("mint")
   if am and bm:econ=(am,ai,bm,bo,"A_TO_B")
  elif bi is not None and ao is not None:
   bm=tm.get(bv,{}).get("mint");am=tm.get(av,{}).get("mint")
   if bm and am:econ=(bm,bi,am,ao,"B_TO_A")
  if not econ:continue
  im,ia,om,oa,direction=econ
  if ia<=0 or oa<=0:continue
  out.append({"family":"METEORA_DAMM_V1","trade_signature":signature,"market_address":pool,
   "trader":trader,"input_asset":im,"input_amount":ia,"output_asset":om,"output_amount":oa,
   "effective_output_per_input":oa/ia,"side":"UNKNOWN_TRADE_TYPE","observed_unix":float(observed_unix),
   "economics_method":"USLS_077_PLUS_082B_DIRECT_TRANSACTION_REPLAY","direction":direction,
   "strict_live_provenance":True,"execution_authority":False})
 return out

def decode_live_trade_extended(family,signature,transaction,observed_unix=None):
 fam=str(family or "").upper()
 if fam=="METEORA_DAMM_V1":return decode_damm_v1(signature,transaction,observed_unix)
 return decode_live_trade(fam,signature,transaction,observed_unix)

def contract():
 return {"revision":"USLS_161Z","supported_families":list(SUPPORTED),
  "newly_supported_family":"METEORA_DAMM_V1","remaining_direct_decoder_pending":["PUMP_FUN"],
  "damm_v1_program_id":CORRECT_PROGRAM,"damm_v1_swap_discriminator_hex":SWAP_DISC.hex(),
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import json,unittest
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161z_phase8_damm_v1_live_decoder_extension import contract
class T(unittest.TestCase):
 def test_contract(self):
  d=contract();print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIn("METEORA_DAMM_V1",d["supported_families"])
  self.assertEqual(d["remaining_direct_decoder_pending"],["PUMP_FUN"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161Z DAMM v1 live decoder extension")
  print("[NEXT] GAP_TARGETED_LIVE_CAPTURE_WITH_DAMM_V1")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
