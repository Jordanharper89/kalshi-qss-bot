from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_lifecycle"
MOD=SUB/"usls_105_phase5_physical_birth_trade_source_census.py"
TEST=ROOT/"test_usls_105_phase5_physical_birth_trade_source_census.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

BIRTH_HINTS=("birth","launch","create","pool_created","pair_created")
TRADE_HINTS=("trade","swap","tape","economic")

def rows(d):
 out=[]
 if not isinstance(d,dict):return out
 for k,v in d.items():
  if isinstance(v,list) and (not v or isinstance(v[0],dict)):
   out.append((k,v))
 return out

def classify(path,key):
 s=(path.name+" "+key).lower()
 if any(x in s for x in BIRTH_HINTS):return "BIRTH"
 if any(x in s for x in TRADE_HINTS):return "TRADE"
 return None

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities";cand=[]
 for p in base.rglob("*.json"):
  try:d=json.loads(p.read_text(encoding="utf-8"))
  except Exception:continue
  for k,v in rows(d):
   c=classify(p,k)
   if not c or not v:continue
   sample=v[0]
   cand.append({"kind":c,"path":str(p.relative_to(root)),"revision":d.get("revision"),
    "list_key":k,"row_count":len(v),"sample_keys":sorted(sample.keys())})
 return {"revision":"USLS_105","candidate_count":len(cand),
  "birth_candidates":sum(x["kind"]=="BIRTH" for x in cand),
  "trade_candidates":sum(x["kind"]=="TRADE" for x in cand),
  "candidates":sorted(cand,key=lambda x:(x["kind"],-x["row_count"],x["path"])),
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_physical_birth_trade_source_census.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_105_phase5_physical_birth_trade_source_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_census(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"candidate_count":d["candidate_count"],"birth_candidates":d["birth_candidates"],"trade_candidates":d["trade_candidates"]},sort_keys=True))
  for x in d["candidates"][:40]:print("[SOURCE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["birth_candidates"],0,"NO_BIRTH_SOURCES_FOUND")
  self.assertGreater(d["trade_candidates"],0,"NO_TRADE_SOURCES_FOUND")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-105 Phase 5 physical birth/trade source census")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
