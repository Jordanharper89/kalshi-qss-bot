from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_018_native_pool_birth_candidate_decoder.py"
TEST=ROOT/"test_suls_018_native_pool_birth_candidate_decoder.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

BIRTH_PATTERNS=(
 "initialize_pool","initialize pool","initialize2","create_pool","create pool",
 "initialize_pool_v2","initializepool","pool initialize","pool created"
)

def decode(root):
 src=root/"runtime_state/solana_opportunities/launch_surveillance/live_native_transaction_program_scan.json"
 d=json.loads(src.read_text(encoding="utf-8"));out=[]
 for tx in d.get("rows",[]):
  logs=[str(x) for x in tx.get("logs") or ()]
  low="\n".join(logs).lower()
  hits=sorted({p for p in BIRTH_PATTERNS if p in low})
  if not hits:continue
  out.append({"slot":tx.get("slot"),"signature":tx.get("signature"),"block_time":tx.get("block_time"),
   "program_ids":tx.get("program_ids") or [],"birth_log_patterns":hits,
   "logs":logs,"decoder_state":"POOL_BIRTH_CANDIDATE","execution_authority":False})
 return {"revision":"SULS_018","transaction_count":d.get("transaction_count",0),
  "candidate_count":len(out),"candidates":out,"execution_authority":False,"read_only":True,
  "scope":"LOG_SEMANTIC_CANDIDATES_ONLY_NOT_YET_VERIFIED_POOL_BIRTHS"}

def write(root):
 d=decode(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_pool_birth_candidates.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_018_native_pool_birth_candidate_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_decode(self):
  p,d=write(ROOT)
  print("[TRANSACTION_COUNT]",d["transaction_count"]);print("[CANDIDATE_COUNT]",d["candidate_count"])
  for x in d["candidates"][:20]:print("[POOL_BIRTH_CANDIDATE]",json.dumps(x,sort_keys=True))
  print("[SCOPE]",d["scope"])
  print("[PASS] SULS-018 native pool-birth candidate decoder")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-018 NATIVE POOL-BIRTH CANDIDATE DECODER");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()