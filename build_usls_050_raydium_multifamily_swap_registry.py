from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_050_raydium_multifamily_swap_registry.py"
TEST=ROOT/"test_usls_050_raydium_multifamily_swap_registry.py"

MOD_TEXT=r"""from __future__ import annotations
import hashlib,json
from pathlib import Path

PROGRAMS={
"RAYDIUM_LAUNCHLAB":"LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj",
"RAYDIUM_V4":"675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
"RAYDIUM_CLMM":"CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
"RAYDIUM_CPMM":"CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"}

def disc(name):return hashlib.sha256(("global:"+name).encode()).digest()[:8].hex()

REGISTRY={
"RAYDIUM_V4":{
 "mode":"U8_TAG","pool_account_index":1,
 "swaps":{"09":"SWAP_BASE_IN","0b":"SWAP_BASE_OUT","10":"SWAP_BASE_IN_V2","11":"SWAP_BASE_OUT_V2"}},
"RAYDIUM_CPMM":{
 "mode":"ANCHOR8","pool_account_index":3,
 "swaps":{disc("swap_base_input"):"SWAP_BASE_INPUT",disc("swap_base_output"):"SWAP_BASE_OUTPUT"}},
"RAYDIUM_CLMM":{
 "mode":"ANCHOR8","pool_account_index":2,
 "swaps":{disc("swap"):"SWAP",disc("swap_v2"):"SWAP_V2"}},
"RAYDIUM_LAUNCHLAB":{
 "mode":"ANCHOR8","pool_account_index":4,
 "swaps":{disc("buy_exact_in"):"BUY_EXACT_IN",disc("buy_exact_out"):"BUY_EXACT_OUT"},
 "coverage_note":"officially verified buy instructions only; sell variants remain decoder-pending"}}

def classify(venue,raw):
 r=REGISTRY[venue];h=raw[:1].hex() if r["mode"]=="U8_TAG" else raw[:8].hex()
 name=r["swaps"].get(h)
 return {"is_exact_swap":name is not None,"instruction_name":name,"key_hex":h,
  "pool_account_index":r["pool_account_index"]}

def write(root):
 d={"revision":"USLS_050","programs":PROGRAMS,"registry":REGISTRY,
  "unknown_instruction_retention":True,"execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_multifamily_swap_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_050_raydium_multifamily_swap_registry import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  self.assertTrue(classify("RAYDIUM_V4",bytes([9])+b"\0"*16)["is_exact_swap"])
  self.assertEqual(classify("RAYDIUM_CPMM",bytes.fromhex("8fbe5adac41e33de"))["instruction_name"],"SWAP_BASE_INPUT")
  self.assertEqual(classify("RAYDIUM_CLMM",bytes.fromhex("2b04ed0b1ac91e62"))["instruction_name"],"SWAP_V2")
  self.assertEqual(classify("RAYDIUM_LAUNCHLAB",bytes.fromhex("faea0d7bd59c13ec"))["instruction_name"],"BUY_EXACT_IN")
  self.assertFalse(classify("RAYDIUM_LAUNCHLAB",b"\xff"*8)["is_exact_swap"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-050 Raydium multi-family exact swap registry")
  print("[PASS] V4/CPMM/CLMM exact swap keys registered; LaunchLab verified buys only")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
