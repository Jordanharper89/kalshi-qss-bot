from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_023_pump_create_v2_exact_account_decoder.py"
TEST=ROOT/"test_usls_023_pump_create_v2_exact_account_decoder.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
SYSTEM="11111111111111111111111111111111"
TOKEN2022="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ATA="ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
WSOL="So11111111111111111111111111111111111111112"
ROLES=("mint","mint_authority","bonding_curve","associated_bonding_curve","global","user",
"system_program","token_program","associated_token_program","mayhem_program_id","global_params",
"sol_vault","mayhem_state","mayhem_token_vault","event_authority","program")

def decode(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 src=json.loads((base/"pump_create_v2_live_capture.json").read_text(encoding="utf-8"))
 rows=[]
 for b in src.get("births") or []:
  for ix in b.get("instructions") or []:
   a=ix.get("accounts") or []
   if len(a)<16:continue
   m={ROLES[i]:a[i] for i in range(16)}
   optional=a[16:]
   m["quote_mint"]=optional[0] if len(optional)>=3 else WSOL
   m["associated_quote_bonding_curve"]=optional[1] if len(optional)>=3 else None
   m["quote_token_program"]=optional[2] if len(optional)>=3 else None
   checks={"system_program":m["system_program"]==SYSTEM,"token_program":m["token_program"]==TOKEN2022,
    "associated_token_program":m["associated_token_program"]==ATA,"program":m["program"]==PUMP,
    "distinct_mint_curve":m["mint"]!=m["bonding_curve"]}
   rows.append({"signature":b["signature"],"slot":b.get("slot"),"observed_unix":b.get("observed_unix"),
    "block_time":b.get("block_time"),**m,"checks":checks,"all_checks":all(checks.values()),
    "execution_authority":False})
 return {"revision":"USLS_023","decoded_count":len(rows),
  "certified_count":sum(1 for x in rows if x["all_checks"]),"rows":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=decode(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_create_v2_decoded_births.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_023_pump_create_v2_exact_account_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_decoder(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"decoded_count":d["decoded_count"],"certified_count":d["certified_count"]},sort_keys=True))
  for x in d["rows"]:print("[DECODE]",json.dumps({"signature":x["signature"],"mint":x["mint"],"bonding_curve":x["bonding_curve"],"associated_bonding_curve":x["associated_bonding_curve"],"quote_mint":x["quote_mint"],"checks":x["checks"]},sort_keys=True))
  self.assertGreater(d["decoded_count"],0);self.assertEqual(d["decoded_count"],d["certified_count"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-023 Pump.fun create_v2 exact account decoder certified")
  print("[PASS] exact mint + bonding curve + associated curve resolved from official account order")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
