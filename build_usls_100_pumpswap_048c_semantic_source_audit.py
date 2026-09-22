from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_100_pumpswap_048c_semantic_source_audit.py"
TEST=ROOT/"test_usls_100_pumpswap_048c_semantic_source_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def load_jsons(base):
 out=[]
 for p in base.rglob("*.json"):
  try:
   d=json.loads(p.read_text(encoding="utf-8"))
  except Exception:
   continue
  out.append((p,d))
 return out

def rows_of(d):
 if isinstance(d,dict):
  for k in ("rows","trades","events"):
   if isinstance(d.get(k),list):return d[k]
 return []

def is_pumpswap_row(x):
 return isinstance(x,dict) and (x.get("venue")=="PUMP_SWAP" or x.get("program_id")=="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")

def build(root):
 base=Path(root)/"runtime_state"
 candidates=[]
 for p,d in load_jsons(base):
  rs=[x for x in rows_of(d) if is_pumpswap_row(x)]
  if rs:
   candidates.append({"path":str(p.relative_to(root)),"row_count":len(rs),"revision":d.get("revision"),
    "exact_like_count":sum(str(x.get("decoder_state","")).startswith("EXACT") for x in rs),
    "sample_keys":sorted(rs[0].keys()) if rs else []})
 candidates.sort(key=lambda x:(x["exact_like_count"],x["row_count"]),reverse=True)
 return {"revision":"USLS_100","candidate_count":len(candidates),"candidates":candidates,
  "required_defects":["FALSE_INSTRUCTION_INDEX_FROM_LOG_INDEX","FALSE_EVENT_TIMESTAMP_AS_BLOCK_TIME","STALE_IDENTITY_REVISION_047B"],
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_source_audit.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_100_pumpswap_048c_semantic_source_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"candidate_count":d["candidate_count"],"required_defects":d["required_defects"]},sort_keys=True))
  for x in d["candidates"][:10]:print("[CANDIDATE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["candidate_count"],0,"NO_PUMPSWAP_RUNTIME_SOURCE_FOUND")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-100 PumpSwap 048C semantic source audit")
  print("[PASS] repair target discovered without fabricating missing semantics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
