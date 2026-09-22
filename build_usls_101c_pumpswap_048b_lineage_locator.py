from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_101c_pumpswap_048b_lineage_locator.py"
TEST=ROOT/"test_usls_101c_pumpswap_048b_lineage_locator.py"

MOD_TEXT=r"""from __future__ import annotations
import json,re
from pathlib import Path

TERMS=("USLS_048B","USLS-048B","047C","PUMP_SWAP","PUMPSWAP","117")

def text_hits(root):
 out=[]
 for base in (Path(root)/"qseries_v2",Path(root)):
  if not base.exists():continue
  for p in base.rglob("*.py"):
   if p.name.startswith("build_usls_101") or p.name.startswith("test_usls_101"):continue
   try:s=p.read_text(encoding="utf-8",errors="ignore")
   except Exception:continue
   score=sum(t.lower() in s.lower() for t in TERMS)
   if score<2:continue
   lines=[]
   for i,line in enumerate(s.splitlines(),1):
    if any(t.lower() in line.lower() for t in TERMS):
     lines.append({"line":i,"text":line[:300]})
   out.append({"path":str(p.relative_to(root)),"score":score,"hits":lines[:40]})
  break
 return sorted(out,key=lambda x:(x["score"],len(x["hits"])),reverse=True)

def json_shapes(root):
 out=[]
 for p in (Path(root)/"runtime_state").rglob("*.json"):
  n=p.name.lower()
  if not any(t in n for t in ("pump","swap","047","048","049")):continue
  try:d=json.loads(p.read_text(encoding="utf-8"))
  except Exception:continue
  shapes=[]
  if isinstance(d,dict):
   for k,v in d.items():
    if isinstance(v,list):shapes.append({"key":k,"len":len(v)})
  out.append({"path":str(p.relative_to(root)),"revision":d.get("revision") if isinstance(d,dict) else None,
   "top_keys":sorted(d.keys())[:50] if isinstance(d,dict) else [],"list_shapes":shapes})
 return sorted(out,key=lambda x:max([z["len"] for z in x["list_shapes"]]+[0]),reverse=True)

def build(root):
 return {"revision":"USLS_101C","source_hits":text_hits(root),"json_candidates":json_shapes(root),
  "target":"LOCATE_ORIGINAL_USLS_048B_117_EXACT_TRADE_LINEAGE",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048b_lineage_locator.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_101c_pumpswap_048b_lineage_locator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_locator(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"source_hits":len(d["source_hits"]),"json_candidates":len(d["json_candidates"])},sort_keys=True))
  for x in d["source_hits"][:15]:print("[SOURCE]",json.dumps(x,sort_keys=True))
  for x in d["json_candidates"][:20]:print("[JSON]",json.dumps(x,sort_keys=True))
  self.assertTrue(d["source_hits"] or d["json_candidates"],"NO_PUMPSWAP_048B_LINEAGE_FOUND")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-101C PumpSwap 048B lineage locator")
  print("[PASS] no semantic certification claimed")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
